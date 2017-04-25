import threading,Pyro4, random,time,math
import Const

lock = threading._RLock


@Pyro4.expose
class Synchronizer():
    """this will synchronize real time among the distributed system
        every configured interval
    """

    def __init__(self):
        """

        :param inteval: time inteval to awake the synchronizer
        """
        self.pyro_ns = Pyro4.naming.locateNS(host="localhost", broadcast=False, port=9090)
        self.interval = random.randint(30,60)
        self.message = []
        t = threading.Thread(target=self.run)
        t.setDaemon(True)
        t.start()

    def is_leader_active(self):
        return Pyro4.Proxy("PYRONAME:"+Const.GATEWAYBACK).get_leader() != None

    def run(self):
        print("Clock synchronizition interval: in {0} seconds".format(self.interval))
        while True:
            time.sleep(self.interval)
            #check if an active leader is present
            if not self.is_leader_active():
                print("Leader not active")
                self.elect_leader()
            #check election success
            if self.is_leader_active():
                if Pyro4.Proxy("PYRONAME:"+Const.GATEWAYBACK).get_leader() == self.name:
                    print("Leader : "+self.name+" starting sync_clock",flush = True)
                    #synchronize clocks among devices and sensors
                    #self.sync_clock()
            else:
                print( "No active nodes can be leader ! " ,flush = True)


    def elect_leader(self):
        """Bully Algorithm
           Pick an arbitrary active node to start election
        """
        #get all devices and sensors
        print(self.name + " starting leader election",flush = True)
        members = self.pyro_ns.list()
        #send election message to each whose id is higher
        try:
            for k in members:
                if k == "Pyro.NameServer" or k == Const.GATEWAYBACK   :  # these two are not members of the multicast group
                    continue
                obj = Pyro4.Proxy(members[k])
                if obj and obj.get_id() > self.get_id():
                    obj.start_election(self.name)

            #wait for election to be end
            time.sleep(Const.ELECTION_TIME)
            #decide winner and let all know
            #checking if OK msg is present
            for k in members:
                if k == "Pyro.NameServer" or k == Const.GATEWAYBACK   :  # these two are not members of the multicast group
                    continue
                obj = Pyro4.Proxy(members[k])
                if obj.get_id() >= self.get_id():
                    if Const.OK not in obj.get_message():
                        #set leader
                        obj.end_election()
        except Exception:
            pass

    def sync_clock(self):
        members = self.pyro_ns.list()
        # send I won msg to everyone
        self.sync_response = []
        for k in members:
            if  k != "Pyro.NameServer" and k != Const.GATEWAYBACK:
                obj = Pyro4.Proxy(members[k])
                obj.report_time(self.name,obj.get_clock())

        while(len(self.get_response()) != len(members)-2):
            time.sleep(0.00000001)
        #calculate clock adjustment
        avg = sum(ele[1] for ele in self.get_response())/len(self.get_response())

        for k in members:
            if k != "Pyro.NameServer" and k != Const.GATEWAYBACK:
                obj = Pyro4.Proxy(members[k])
                obj.set_clock(avg)


    def end_election(self):
        #set leader
        Pyro4.Proxy("PYRONAME:"+Const.GATEWAYBACK).set_leader(self.name)
        # send winning message to all
        members = self.pyro_ns.list()
        #send I won msg to everyone
        for k in members:
            if k != "Pyro.NameServer" and k != Const.GATEWAYBACK:
                obj = Pyro4.Proxy(members[k])
                obj.send_message(self.name, Const.I_WON)


    def start_election(self, name):
        # to store received election message, for later checking who is leader
        # upon receiving msg, send OK, but not to itself
        self.message = []
        if name != self.name:
            print("Received start-election-msg from {0}".format( name),flush = True)
            obj = self.get_remote_obj(name)
            obj.send_message(self.name, Const.OK)
        #send election to each device or sensor of higher ID
        members = self.pyro_ns.list()
        for k in members:
            if k == "Pyro.NameServer" or k == Const.GATEWAYBACK:  # these two are not members of the multicast group
                continue
            obj = Pyro4.Proxy(members[k])
            if obj.get_id() > self.get_id():
                    obj.start_election()

    def send_message(self, name, msg):
        if msg == Const.OK:
            print("Received OK from {0} ".format(name),flush = True)
            self.get_message().append(Const.OK)
        if msg == Const.I_WON:
            print("Recognising {0} as leader".format(name),flush = True)

    def get_remote_obj(self,name):
        return Pyro4.Proxy("PYRONAME:"+name)

    def report_time(self,leader_name,leader_clock):
        obj = self.get_remote_obj(leader_name)
        obj.get_response().append(self.clock-leader_clock)

    def get_message(self):
        return self.message

    def get_response(self):
        return self.sync_response