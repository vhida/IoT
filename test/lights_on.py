import Pyro4, Pyro4.naming, sys, threading, time
sys.path.append('./src')
from message import NodeECState, MsgType

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

def user_enter_via_gatewayfront(pid, state):
	Pyro4.Proxy(pyro_ns.lookup("gateway")).change_state(pid, state)

def setclockmodes():
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).setclockmode(MODE)

def lights_on():
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).toggle_state("NO")
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).toggle_state("YES")
	time.sleep(3) #simulate that person is in room and lights on for 3s
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).toggle_state("NO")

MODE = "LOGICAL"
#set which clock sync mode to use real or logical
#set the clock mode for all sensors and devices
print("Preparing and initializing...")
setclockmodes()
reset()
time.sleep(5)
if MODE == "REAL":
	setleader("gateway")
	time.sleep(5)
	#wait for leader election to run and berkeley to complete before exchanging messages


start_time = time.time()
print("Starting simulation at {0}".format(start_time))
lights_on()
end_time = time.time()
print("End simulation at {0}".format(end_time))
print("Duration {0}".format(end_time - start_time))