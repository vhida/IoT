import Pyro4, Pyro4.naming, threading, time, sys, random, queue, heapq
from message import MsgType, Message

sys.excepthook = Pyro4.util.excepthook
Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'

_msgseq_lock = threading.Lock()
_logclock_lock = threading.Lock()
_msgack_lock = threading.Lock()

@Pyro4.expose
class LogicalProcess():
	def __init__(self):
		#each logicalclock starts at a different offset time and has a different tick rate(due to different crystal value)
		self.logicalclock = 0	#incrementing variable
		self.msg_acks = {}	#store message acks corresponding to each (msgid, frompid)
		self.msg_seq = 0	#sequentially incrementing sequence number
		self.msg_queue = queue.PriorityQueue()
		self.rcvdmsg_q = queue.Queue()
		self.msghist = {}	#mg history of seen msgid

		#start the queue reader as a deamon which gets message
		t = threading.Thread(target = self.buffered_msg_queue_reader)
		t.setDaemon(True)
		t.start()
		#buffere reader daemon
		t2 = threading.Thread(target = self.rcvd_msg_queue_reader)
		t2.setDaemon(True)
		t2.start()
		
	def getId(self):
		return self.id

	# a multicast is implemented as N unicasts
	def multicast(self, msg):
		if msg.msg_type == MsgType.STATE:
			print("logical ts {0} SEND event {1}".format(msg.ts_logical, msg))

		#print("sending a multicaast {0}".format(msg), flush=True)
		members =  self.pyro_ns.list()
		for k in members:
			if k == "Pyro.NameServer" or k == "db":#these two are not members of the multicast group
				continue
			Pyro4.Proxy(members[k]).rcv(msg)	

	#after buffering once a message is ready to be processed it comes here
	def deliver(self, msg):
		#print("got message {0}".format(msg), flush=True)
		if msg.msg_type == MsgType.DATA or msg.msg_type == MsgType.STATE:
			self.msg_queue.put(msg)
			self.setlogclock(max(self.logicalclock, msg.ts_logical) + 1)
			print("logical ts {0} RCVD {1}".format(self.logicalclock, msg))
			nmsg = Message(id = self.getNextMsgId(), pid = self.id, data = (msg.msgid, msg.frompid), msg_type = MsgType.ACK, ts_logical = msg.ts_logical)
			self.multicast(nmsg)
		#send message acks
		elif msg.msg_type == MsgType.ACK:
			global _msgack_lock
			with _msgack_lock:
				curval = self.msg_acks.get(msg.data, 0)
				self.msg_acks[msg.data] = curval + 1

	#a message whose msgid doesn't correspond to the next expected message id is buffered
	def rcvd_msg_queue_reader(self):
		while 1:
			msg = self.rcvdmsg_q.get()
			if msg.msgid == self.msghist.get(msg.frompid, 0) + 1:
				self.msghist[msg.frompid] = self.msghist.get(msg.frompid, 0) + 1
				self.deliver(msg)
			else:
				self.rcvdmsg_q.put(msg)
				
	def rcv(self, msg):
		self.rcvdmsg_q.put(msg)
	
	#applayer method which consumes an event
	def consume_event(self, msg):
		if msg.msg_type == MsgType.STATE:
			self.report_state(msg.frompid, msg)

	# a message is buffered unitl is not ACKed by all the other processes
	def buffered_msg_queue_reader(self):
		while 1:
			#blocks untill a message is available
			msg = self.msg_queue.get()
			members = self.pyro_ns.list()
			global _msgack_lock
			with _msgack_lock:
				if self.msg_acks.get((msg.msgid, msg.frompid), 0) == len(members) - 2:
					self.consume_event(msg)
				else:
					#add it back into the queue
					self.msg_queue.put(msg)

	#set log clock
	def setlogclock(self, logclock):
		global _logclock_lock
		with _logclock_lock:
			self.logicalclock = logclock
	
	#atomic operation to get next logical clock value, currently it is set to increment by 1 for even PID and 2 for odd PID
	def getNextLogts(self):
		global _logclock_lock
		with _logclock_lock:
			#the clock tick rate is different for each process (currently set the tick rate at 2*id of clock)
			self.logicalclock += ((self.id % 2) + 1)
			ts = self.logicalclock
		return ts

	#atomic operation implemented using locks to get next msg sequence number
	def getNextMsgId(self):
		global _msgseq_lock
		with _msgseq_lock:
			self.msg_seq += 1
			seqnum = self.msg_seq
		return seqnum

	#clear local buffers and list before start of new testcase
	def reset(self):
		self.msg_seq = 0
		self.msghist.clear()
		self.msg_acks.clear()

	#set clock mode to be either LOGICAL or REAL
	def setclockmode(self, mode):
		self.clock_mode = mode
		print("Clock mode set to {0}".format(self.clock_mode))
		