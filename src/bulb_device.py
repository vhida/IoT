import Pyro4, Pyro4.naming, threading, time, sys, random, queue, socket
from message import MsgType, Message

from logicalprocess import LogicalProcess
from realprocess import RealProcess
from electionprocess import ElectionProcess

sys.excepthook = Pyro4.util.excepthook

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Bulb_device(LogicalProcess, RealProcess, ElectionProcess):
	def __init__(self, stype, name, comtype):
		global ns_name, ns_port
		self.pyro_ns = Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port)

		LogicalProcess.__init__(self)
		RealProcess.__init__(self)
		self.state = None
		self.stype = stype
		self.comtype = comtype
		self.name = name
		self.register()

	def register(self):
		self.id = Pyro4.Proxy(self.pyro_ns.lookup("gateway")).register(self.stype, self.name)
		print("Id {0}".format(self.id))
		#method definition modified since only gateway has the ability to register other sensors/devices

	def query_state(self, id):
		return (self.id, self.state)

	def report_state(self, id, val):
		if id == self.id:
			self.state = val.data
		print("ts-logical: {0} ts-real: {1} DELIVERED {2}".format(self.getNextLogts(), self.getNextRealts(), val))
		
	def change_state(self, id, state):
		pass
		#no method implementation

	def toggle_state(self, new_state):
		self.state = new_state
		print("Bulb is switched: {0}".format(new_state))

if __name__=="__main__":
	global ns_name, ns_port
	nsinfo = sys.argv[1]
	ns_name = nsinfo.split(":")[0]
	ns_port = int(nsinfo.split(":")[1])
	obj = Bulb_device("Device", "Bulb", "NA")
	print("Device: {0} assigned id: {1} running with below uri.".format(obj.name, obj.id), flush=True)
	#replace nameserver with valid host and port instead of localhost
	with Pyro4.core.Daemon(host=socket.gethostbyname(socket.gethostname())) as daemon:
		with Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port) as ns:
			uri = daemon.register(obj, obj.stype + "." + obj.name)
			print(uri, flush=True)
			ns.register(obj.stype + "." + obj.name, uri)
		#make a new thread, daemon-true
		daemon.requestLoop()