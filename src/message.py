from enum import Enum

class NodeECState(Enum):
    PARTICIPANT = 1
    NON_PARTICIPANT = 2
    LEADER = 3
    
class MsgType(Enum):
    ACK = 1
    DATA = 2
    STATE = 3
    ELECTION = 4
    LEADER = 5

class Message(object):
    def __init__(self, data, msg_type, pid, id=None, ts=None, ts_logical=None):
        self.msgid = id
        self.frompid = pid
        self.data = data
        self.msg_type = msg_type
        self.ts = ts
        self.ts_logical = ts_logical
        
    def __lt__(self, msg):
        if self.ts_logical < msg.ts_logical:
            return True
        elif self.ts_logical > msg.ts_logical:
            return False
        else:
            return self.frompid < msg.frompid
        
    def __repr__(self):
        return "(id:{0},{1},data: {2}, lts: {3}, realts: {4}, from:{5})".format(self.msgid, self.msg_type, self.data, self.ts_logical, self.ts, self.frompid)

    def __str__(self):
        return "(id:{0},{1},data: {2}, lts: {3}, realts: {4}, from:{5})".format(self.msgid, self.msg_type, self.data, self.ts_logical, self.ts, self.frompid)