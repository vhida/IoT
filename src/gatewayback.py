import threading, Pyro4, Pyro4.naming, sys, time, collections, socket
from logicalprocess import LogicalProcess
from realprocess import RealProcess
sys.excepthook = Pyro4.util.excepthook

@Pyro4.expose
@Pyro4.behavior(instance_mode = "single")
class GatewayBack(LogicalProcess, RealProcess):
	def __init__(self):
		global ns_name, ns_port
		self.pyro_ns = Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port)

		LogicalProcess.__init__(self)
		RealProcess.__init__(self)
		self.id = 1
		self.iskey = False
		#ordered dict so that every time we print to file in same order
		self.states = collections.OrderedDict()
		#initial states of the devices/sensor is set to NA
		self.states["Motion"] = "NA"
		self.states["Door"] = "NA"
		self.states["Temperature"] = "NA"
		self.states["Bulb"] = "NA"
		self.states["Outlet"] = "NA"
		#the file handle to our backend storage
		self.filehandle = open("db.txt", "w")
		self.leader = None
		self.proids = {}
		self.fsm = 0
		self.add_record(0, 0)

	def change_state(self, pid, new_state):
		pass

	def register(self, pid, pname):
		self.proids[pid] = pname

	def query_state(self, pid):
		return self.states[pid]

	def report_state(self, pid, val):
		# a finite state machine which has no storage except for one variable 'fsm'
		if self.proids[pid] == "Door" and val.data == "KEY":
			self.iskey = True
		elif self.fsm == 0 and self.proids[pid] == "Door" and val.data == "OPEN":
			self.fsm = 1
		elif self.fsm == 1 and self.proids[pid] == "Motion" and val.data == "YES":
			self.fsm = 2
		elif self.fsm == 2 and self.proids[pid] == "Door" and val.data == "CLOSED":
			self.fsm = 3
		elif self.fsm == 3 and self.proids[pid] == "Motion" and val.data == "NO":
			self.fsm = 4
		else:
			self.fsm = 0

		self.states[self.proids[pid]] = val.data

		#for each state change a record is added to the database
		self.add_record(val.ts, val.ts_logical)
		if self.fsm == 4:
			self.fsm = 0
			if self.iskey:
				self.add_msg("MSG: User Enters House, MODE: HOME, SECURTIY: DISABLED \n")
				self.iskey = False
			else:
				self.add_msg("MSG: Theif Enters House, ALARM RING !! \n")

	def add_msg(self, msg):
		self.filehandle.write(msg)
		self.filehandle.flush()

	def add_record(self, ts, ts_logical):
		val = ""
		for k in self.states:
			val += "{0}:{1} ".format(k, self.states[k])
		line = val + "logical_clock:" + str(ts_logical) + " real_clock:" + str(ts) + "\n"
		self.filehandle.write(line)
		self.filehandle.flush()

	def get_leader(self):
		return self.leader

	def set_leader(self,name):
		self.leader = name

if __name__ == '__main__':
	global ns_name, ns_port
	nsinfo = sys.argv[1]
	ns_name = nsinfo.split(":")[0]
	ns_port = int(nsinfo.split(":")[1])

	print("db running with below uri: ")
	gtback = GatewayBack()
	
	with Pyro4.core.Daemon(host=socket.gethostbyname(socket.gethostname())) as daemon:
		with Pyro4.naming.locateNS(host=ns_name, broadcast=False, port=ns_port) as ns:
			uri = daemon.register(gtback, "db")
			print(uri)
			ns.register("db", uri)
		daemon.requestLoop()