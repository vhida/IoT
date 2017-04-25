import Pyro4, Pyro4.naming, sys, threading, time
sys.path.append('./src')
from message import NodeECState

sys.excepthook = Pyro4.util.excepthook
Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'

nsinfo = sys.argv[1]
ns_name = nsinfo.split(":")[0]
ns_port = int(nsinfo.split(":")[1])
pyro_ns = Pyro4.locateNS(host=ns_name, port=ns_port)

#set the leader of the cluster
def setleader(name):
	Pyro4.Proxy(pyro_ns.lookup(name)).setnodestate(NodeECState.LEADER)

def reset():
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).reset()

#set the clock mode for all sensors and devices
def setclockmodes():
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Door")).setclockmode(MODE)
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).setclockmode(MODE)
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Temperature")).setclockmode(MODE)

def door_test(dt):	
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Door")).toggle_state(dt)
	
def motion_test(dt):
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).toggle_state(dt)

def temperature_test(dt):	
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Temperature")).toggle_state(dt)


#set which clock sync mode to use real or logical
MODE = "LOGICAL"
setclockmodes()
reset()

if MODE == "REAL":
	setleader("gateway")
	time.sleep(5)
	#wait for leader election to run and berkeley to complete before exchanging messages

cmd = int(input("num of commands:"))
print(cmd)
while cmd > 0:
	line = input("command:")
	print(line)
	sensor, value = line.split(" ")
	if sensor == "door":
		t = threading.Thread(target = door_test, args = (value,))
	elif sensor == "motion":
		t = threading.Thread(target = motion_test, args = (value,))
	elif sensor == "temperature":
		t = threading.Thread(target = temperature_test, args = (value,))
	
	t.start()
	cmd -= 1