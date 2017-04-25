import Pyro4, Pyro4.naming, sys, threading, time
sys.excepthook = Pyro4.util.excepthook
Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'

#This test will check if messages sent by a single sender are delivered to all members of the multicast in the same order
#simulated as a serious of temperature changes
def reset():
	pyro_ns = Pyro4.naming.locateNS(host="localhost", broadcast=False, port=9090)
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).reset()

def setclockmodes():
	pyro_ns = Pyro4.naming.locateNS(host="localhost", broadcast=False, port=9090)
	members =  pyro_ns.list()
	for k in members:
		if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
			continue
		Pyro4.Proxy(members[k]).setclockmode(MODE)

def tempChange(dt):
	Pyro4.Proxy("PYRONAME:Sensor.Temperature").toggle_state(dt)

MODE = "REAL"
print("Preparing and initializing...")
setclockmodes()
reset()

time.sleep(10)

for temp in ["34F", "40F", "29F", "60F", "61F", "45F", "41F"]:
	tempChange(temp)