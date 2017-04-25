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

def startelection():
	Pyro4.Proxy(pyro_ns.lookup("Sensor.Motion")).start_election()

start_time = time.time()
print("Starting simulation at {0}".format(start_time))
startelection()
end_time = time.time()
print("End simulation at {0}".format(end_time))
print("Durationi {0}".format(end_time - start_time))