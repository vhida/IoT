import Pyro4, Pyro4.naming, threading, time, sys, random, queue, heapq
from message import MsgType, Message, NodeECState

sys.excepthook = Pyro4.util.excepthook
Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'

_realclock_lock = threading.Lock()

@Pyro4.expose
class RealProcess():
	def __init__(self):
		self.clock = round(time.time() % 100)
		print("init real clock value: {0}".format(self.clock))
		self.nodestate = None
		self.msg_queue_realts = queue.PriorityQueue()		
		#the berkeley time daemon which runs continously to sync real clock values
		t = threading.Thread(target = self.timeDaemon)
		t.setDaemon(True)
		t.start()
		#priority queue reader
		t2 = threading.Thread(target = self.rcv_real_ts_buffer_reader)
		t2.setDaemon(True)
		t2.start()

	def rcv_real_ts_buffer_reader(self):
		while 1:
			msg = self.msg_queue_realts.get()[1]
			self.report_state(msg.frompid, msg)

	def rcv_realts(self, msg):
		self.msg_queue_realts.put((msg.ts, msg))

	def setnodestate(self, state):
		self.nodestate = state

	def timeDaemon(self):
		while 1:
			#clock is synchronized every 1/10 secs
			if self.nodestate != NodeECState.LEADER:
				#sleep for an additional 3s while clocks are synchronized and then continue
				time.sleep(3)
				continue
			else:
				#i am the leader, so run berkeley algorithm
				self.berkeleySync()
			time.sleep(1/10)

	def berkeleySync(self):
		proxies = {}
		members = self.pyro_ns.list()
		#keep track of machhines which are down and skip them when performing berkeley algorithm sync
		down_machines = []
		for k in members:
			if k == "Pyro.NameServer" or k == "db":
				continue
			#this doesn't throw an error u can create proxies to dead processes
			proxies[k] = Pyro4.Proxy(members[k])

		avgtime = 0
		for k in proxies:
			if k in down_machines:
				continue
			try:
				#only calling methods on dead proxies is a problem
				start_time = time.time()
				avgtime += proxies[k].getRealts()
				end_time = time.time()
				#we consider the network delay while computing the avg time as well
				delay = (end_time - start_time)/2
				avgtime += delay
			except Exception:
				#log is printed if a node is down, to remind user to start the node
				if k not in down_machines:
					print("node {0} is down".format(members[k]), flush=True)
					down_machines.append(k)					
		
		avgtime = avgtime/len(proxies)
		avgtime = round(avgtime)
		for k in proxies:
			if k == "Pyro.NameServer" or k == "db":
				continue
			if k in down_machines:
				continue
			proxies[k].setRealts(avgtime)

	#setter method for the real clock
	def setRealts(self, new_clock):
		global _realclock_lock
		with _realclock_lock:
			self.clock = new_clock

	#getter method for the real clock
	def getRealts(self):		
		return self.clock

	#atomic operation for increment of real clock value (currently it increments it by the self.id value)
	def getNextRealts(self):
		global _realclock_lock
		with _realclock_lock:
			#the clock tick rate is different for each process (currently set the tick rate at 2*id of clock)
			self.clock += (self.id + 1)
			ts = self.clock
		return ts
