import Pyro4, Pyro4.naming, threading, time, sys, socket
from message import MsgType, Message
from logicalprocess import LogicalProcess
from realprocess import RealProcess
from electionprocess import ElectionProcess
sys.excepthook = Pyro4.util.excepthook

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Door_sensor(LogicalProcess, RealProcess, ElectionProcess):
	def __init__(self, stype, name, comtype):
		global ns_name, ns_port
		self.pyro_ns = Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port)
		self.state = None
		self.stype = stype
		self.comtype = comtype
		self.name = name
		self.register()
		LogicalProcess.__init__(self)
		RealProcess.__init__(self)
		
	def register(self):
		self.id = Pyro4.Proxy(self.pyro_ns.lookup("gateway")).register(self.stype, self.name)
		print("Id {0}".format(self.id))
		#method definition modified since only gateway has the ability to register other sensors/devices

	def query_state(self, id):
		#in a pull based sensor, gateway calls this method via RPC to get state info
		return (self.id, self.state)

	def report_state(self, id, val):
		if id == self.id:
			self.state = val.data
		print("logical ts {0} real ts {1} DELIVERED {2}".format(self.getNextLogts(), self.getNextRealts(), val))
		#no method implementation
		#a sensor doesn't keep track of states
		
	def change_state(self, id, state):
		pass
		#no method implementation
		#sensor doesn't have capability to change state of another device

	# -- util methods being --
	def push_data(self, msg):
		#push data via calling report_state on the gateway
		print("real ts {0} SEND event {1}".format(msg.ts, msg))
		Pyro4.Proxy(self.pyro_ns.lookup("gateway")).rcv_realts(msg)

	def toggle_state(self, msgdata):
		msg = Message(id = self.getNextMsgId(), pid = self.id, data = msgdata, msg_type = MsgType.STATE, ts = self.getNextRealts(), ts_logical = self.getNextLogts() )
		if self.comtype == "push":
			if self.clock_mode == "LOGICAL":
				self.multicast(msg)
			else:
				self.push_data(msg)


if __name__=="__main__":
	global ns_name, ns_port
	nsinfo = sys.argv[1]
	ns_name = nsinfo.split(":")[0]
	ns_port = int(nsinfo.split(":")[1])
	obj = Door_sensor("Sensor", "Door", "push")
	print("Sensor: {0} running with below uri: ".format(obj.name), flush=True)
	#replace nameserver with valid host and port instead of localhost
	with Pyro4.core.Daemon(host=socket.gethostbyname(socket.gethostname())) as daemon:
		with Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port) as ns:
			uri = daemon.register(obj, obj.stype + "." + obj.name)
			print(uri)
			ns.register(obj.stype + "." + obj.name, uri)
		#make a new thread, daemon-true
		daemon.requestLoop()