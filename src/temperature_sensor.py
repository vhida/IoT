import Pyro4, Pyro4.naming, threading, time, sys, socket
from message import MsgType, Message
from logicalprocess import LogicalProcess
from electionprocess import ElectionProcess
from realprocess import RealProcess
sys.excepthook = Pyro4.util.excepthook


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Temperature_sensor(LogicalProcess, RealProcess, ElectionProcess):
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
		print("Id {0}".format(self.id))

	def register(self):
		self.id = Pyro4.Proxy(self.pyro_ns.lookup("gateway")).register(self.stype, self.name)

	#in a pull based sensor, gateway calls this method via RPC to get state info
	def query_state(self, id):
		return (self.id, self.state)

	def report_state(self, id, val):
		print("ts-logical: {0} ts-real: {1} DELIVERED {2}".format(self.getNextLogts(), self.getNextRealts(), val))
		#no method implementation
		#a sensor doesn't keep track of states
		
	def change_state(self, id, state):
		pass
		#no method implementation
		#sensor doesn't have capability to change state of another device

	# -- util methods being --
	def push_data(self, msg):
		#push data via calling report_state on the gateway
		print("real ts: {0} SEND event {1}".format(msg.ts, msg))
		Pyro4.Proxy(self.pyro_ns.lookup("gateway")).rcv_realts(msg)

	def toggle_state(self, new_state):
		if self.comtype == "push":
			msg = Message(id = self.getNextMsgId(), pid = self.id, data = new_state, msg_type = MsgType.STATE, ts = self.getNextRealts(), ts_logical = self.getNextLogts() )
			if self.clock_mode == "LOGICAL":
				self.multicast(msg)
			else:
				self.push_data(msg)

if __name__=="__main__":
	global ns_name, ns_port
	nsinfo = sys.argv[1]
	ns_name = nsinfo.split(":")[0]
	ns_port = int(nsinfo.split(":")[1])
	
	obj = Temperature_sensor("Sensor", "Temperature", "push")
	print("Sensor: {0} running with below uri: ".format(obj.name), flush=True)

	with Pyro4.core.Daemon(host=socket.gethostbyname(socket.gethostname())) as daemon:
		with Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port) as ns:
			uri = daemon.register(obj, obj.stype + "." + obj.name)
			print(uri, flush=True)
			ns.register(obj.stype + "." + obj.name, uri)
		#make a new thread, daemon-true
		daemon.requestLoop()