import Pyro4, Pyro4.naming, threading, time, sys, random, queue, heapq
from message import MsgType, Message, NodeECState

sys.excepthook = Pyro4.util.excepthook
Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'

@Pyro4.expose
class ElectionProcess():
	def __init__(self):
		pass

	#returns the next live sucessor (next greater process ID) in the group of live nodes
	def getSucessor(self, prevId = None):
		nxtId = self.id + 1
		if prevId is not None:
			#base case of recursion, if you end up with your own id declare self as LEADER
			if prevId == self.id:
				self.nodestate = NodeECState.LEADER
				return self.id
			nxtId = prevId + 1

		num = len(self.pyro_ns.list()) - 3
		highestId = num + 2
		
		#wrap around if you are at the end of the ring
		if nxtId > highestId:
			nxtId = 2
		
		#id 2 is reserved for frontend gateway always
		if nxtId == 2:
			return "gateway"
		else:
			(ptype, pname) = Pyro4.Proxy(self.pyro_ns.lookup("gateway")).getAddrFor(nxtId)
			try:
				isalive = Pyro4.Proxy(self.pyro_ns.lookup(ptype + "." + pname)).getLiveStatus()
				if isalive:
					return (ptype, pname)
				else:
					#recursive call if did not get sucessor yet
					return self.getSucessor(nxtId)
			except Exception:
				print("my sucessor {0} is down...trying next".format((ptype, pname)))
				#recursive call if did not get sucessor yet
				return self.getSucessor(nxtId)

	#heartbeet check fundtion to determine if a node is live
	def getLiveStatus(self):
		return True

	#calling this function starts the leader election
	def start_election(self):
		print("starting election at {0}".format(self.id))
		nmsg = Message([self.id], MsgType.ELECTION, self.id)
		nxtId = self.getSucessor()
		#list of messages is maintained in the msg.data array list
		print("got sucessor {0}".format(nxtId))
		if nxtId != self.id:
			if nxtId == "gateway":
				Pyro4.Proxy(self.pyro_ns.lookup("gateway")).elect_rcv(nmsg)
			else:	
				Pyro4.Proxy(self.pyro_ns.lookup(nxtId[0] + "." + nxtId[1])).elect_rcv(nmsg)

	#the basic communication method for passing election, leader messages from one process to another
	def elect_rcv(self, msg):
		print("got message {0}".format(msg))
		if msg.msg_type == MsgType.ELECTION:
			if self.id in msg.data:
				#message has gone a circle already
				leader = max(msg.data)
				nmsg = Message([self.id], MsgType.LEADER, self.id, id = leader)
				nxtId = self.getSucessor()
				print("got sucessor {0}".format(nxtId))
				if nxtId != self.id:
					if nxtId == "gateway":
						Pyro4.Proxy(self.pyro_ns.lookup("gateway")).elect_rcv(nmsg)
					else:	
						Pyro4.Proxy(self.pyro_ns.lookup(nxtId[0] + "." + nxtId[1])).elect_rcv(nmsg)
			else:
				msg.data.append(self.id)
				#append self.id and forward message to sucessor
				nxtId = self.getSucessor()
				print("got sucessor {0}".format(nxtId))
				if nxtId != self.id:
					nmsg = Message(msg.data, MsgType.ELECTION, self.id)
					if nxtId == "gateway":
						Pyro4.Proxy(self.pyro_ns.lookup("gateway")).elect_rcv(nmsg)
					else:	
						Pyro4.Proxy(self.pyro_ns.lookup(nxtId[0] + "." + nxtId[1])).elect_rcv(nmsg)

		elif msg.msg_type == MsgType.LEADER:
			if self.id in msg.data:
				#ok i got the leader drop the message now
				print("election complete")
			else:			
				#leader if is stored in self.leaderid
				self.leaderid = msg.msgid
				if self.leaderid == self.id:
					self.nodestate = NodeECState.LEADER
					print("i am the leader")
				else:
					self.nodestate = NodeECState.PARTICIPANT
				#upon completetion of leader election each process or node is either a LEADER or PARTICIPANT
				print("leader is:{0}".format(self.leaderid))

				nxtId = self.getSucessor()
				print("got sucessor {0}".format(nxtId))
				msg.data.append(self.id)

				if nxtId != self.id:
					if nxtId == "gateway":
						Pyro4.Proxy(self.pyro_ns.lookup("gateway")).elect_rcv(msg)
					else:	
						Pyro4.Proxy(self.pyro_ns.lookup(nxtId[0] + "." + nxtId[1])).elect_rcv(msg)
