import Pyro4, Pyro4.naming, sys, threading, time
sys.excepthook = Pyro4.util.excepthook
Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'

nsinfo = sys.argv[1]
ns_name = nsinfo.split(":")[0]
ns_port = int(nsinfo.split(":")[1])
pyro_ns = Pyro4.locateNS(host=ns_name, port=ns_port)
#This test will check if messages sent by a single sender are delivered to all members of the multicast in the same order
#simulated as a serious of temperature changes
def reset():
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).reset()

def setclockmodes():	
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).setclockmode(MODE)

def tempChange(dt):
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Temperature")).toggle_state(dt)

MODE = "LOGICAL"
print("Preparing and initializing...")
setclockmodes()
reset()

time.sleep(10)

t1 = threading.Thread(target = tempChange, args=("34F",))
t2 = threading.Thread(target = tempChange, args=("40F",))
t3 = threading.Thread(target = tempChange, args=("29F",))
t4 = threading.Thread(target = tempChange, args=("60F",))
t5 = threading.Thread(target = tempChange, args=("61F",))
t6 = threading.Thread(target = tempChange, args=("45F",))
t7 = threading.Thread(target = tempChange, args=("41F",))

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()
t7.start()