import Pyro4, Pyro4.naming, sys, threading, time
sys.path.append('./src')
from message import NodeECState, MsgType

sys.excepthook = Pyro4.util.excepthook
Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'

def get_current_states():
	gtfront = Pyro4.Proxy(pyro_ns.lookup("gateway"))
	for k in ["Door", "Temperature", "Motion", "Bulb", "Outlet"]:
		print("State of {0} is {1}".format(k, gtfront.query_state(k)))

start_time = time.time()
print("Starting simulation at {0}".format(start_time))
get_current_states()
end_time = time.time()
print("End simulation at {0}".format(end_time))
print("Duration {0}".format(end_time - start_time))