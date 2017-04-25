import Pyro4, Pyro4.naming, sys, random, threading, socket
from message import MsgType, Message

from logicalprocess import LogicalProcess
from realprocess import RealProcess
from electionprocess import ElectionProcess

_ids_lock = threading.Lock()
sys.excepthook = Pyro4.util.excepthook

@Pyro4.expose
@Pyro4.behavior(instance_mode = "single")
class GatewayFront(LogicalProcess, RealProcess, ElectionProcess):
	def __init__(self):
		global ns_name, ns_port
		self.pyro_ns = Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port)

		LogicalProcess.__init__(self)
		RealProcess.__init__(self)

		self.id = 2
		self._processids = {}
		#an incrementing sequence to assign ids to devices and processes
		self._ids = 2
		#create an instance of the backend, it will be a shared proxy
		self._dbproxy = Pyro4.Proxy(self.pyro_ns.lookup("db"))
		print("Id {0}".format(self.id))

	# a method which enables other process to register with the gateway and get a PID
	def register(self, ptype, pname):
		pid = self.getNextPid()
		self._processids[pid] = (ptype, pname)
		self._dbproxy.register(pid, pname)
		return pid

	def query_state(self, pid):
		#get current state from db and report
		return self._dbproxy.query_state(pid)			

	# a name to pid translation service
	def nametopid(self, name):
		for k in self._processids:
			if self._processids[k][1] == name:
				return k

	def report_state(self, pid, val):
		msg_ts = self.getNextRealts()
		msg_ts_logical = self.getNextLogts()
		print("ts-logical: {0} ts-real: {1} DELIVERED {2}".format(msg_ts_logical, msg_ts, val))
		#forward the update mesaage to the backend db
		if pid != self.id:
			val.ts = msg_ts
			val.ts_logical = msg_ts_logical
			self._dbproxy.report_state(pid, val)
			cpname = self._processids[pid][1]
			if cpname == "Motion" and val.msg_type == MsgType.STATE and val.data == "YES":
				bulb = self.nametopid("Bulb")
				print("Gateway Remotely switiching ON bulb")
				#sending a remote message to remotely turno ON the bulb
				self.change_state(bulb, "ON")
			elif cpname == "Motion" and val.msg_type == MsgType.STATE and val.data == "NO":
				bulb = self.nametopid("Bulb")
				print("Gateway Remotely switiching OFF bulb")
				#sending a remote message to remotely turno OFF the bulb
				self.change_state(bulb, "OFF")

	#the frontend gateway has ability to toggle the state of another device/sensor and control it remotely
	def change_state(self, pid, new_state):
		if pid in self._processids:
			Pyro4.Proxy(self.pyro_ns.lookup(self._processids[pid][0] + "." + self._processids[pid][1])).toggle_state(new_state)
			if pid != self.id:
				nmsg = Message(new_state, MsgType.STATE, pid)
				#self._dbproxy.report_state(pid, nmsg)

	# atomic operation to icnrement prcess PID which is assigned to different proceses
	def getNextPid(self):
		global _ids_lock
		with _ids_lock:
			self._ids += 1
			pid = self._ids
		return pid

	#since all process register with the frontend gateway
	#it exposes an API for others to get address of a process ID
	def getAddrFor(self, id):
		if id == 1:
			return "db"
		elif id == 2:
			return "gateway"
		else:
			return self._processids[id]

if __name__ == '__main__':
	global ns_name, ns_port
	nsinfo = sys.argv[1]
	ns_name = nsinfo.split(":")[0]
	ns_port = int(nsinfo.split(":")[1])

	print("gateway running with below uri: ",flush=True)
	gtfront = GatewayFront()

	with Pyro4.core.Daemon(host=socket.gethostbyname(socket.gethostname())) as daemon:
		with Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port) as ns:
			uri = daemon.register(gtfront, "gateway")
			print(uri, flush=True)
			#print "URI is : ", uri
			ns.register("gateway", uri)
		daemon.requestLoop()