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

#reset each node before begining the test case simulation
def reset():
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).reset()

# set the clock synchronziation approach to use 
# LOGICAL uses totally ordered multicast, REAL uses Berkeley Algorithm 
def setclockmodes():
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).setclockmode(MODE)

def thief_enter():
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Door")).toggle_state("OPEN")
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).toggle_state("YES") 
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Door")).toggle_state("CLOSED")
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).toggle_state("NO")

MODE = "LOGICAL"
#set which clock sync mode to use real or logical
#set the clock mode for all sensors and devices
print("Preparing and initializing...")
setclockmodes()
reset()

if MODE == "REAL":
	setleader("gateway")
	time.sleep(5)
	#wait for leader election to run and berkeley to complete before exchanging messages

start_time = time.time()
print("Starting simulation at {0}".format(start_time))
thief_enter()
end_time = time.time()
print("End simulation at {0}".format(end_time))
print("Durationi {0}".format(end_time - start_time))