## Source files

All the files are in the src directory

1. `x_sensor.py` names are given to all sensors
2. `x_device.py` names are given to all devices
3. `gatewayfront.py` is the name assigned to the frontend gateway
4. `gatewayback.py` is the name assigned to the backend gateway
5. `message.py` contains the common message wrapper which we use as the payload when passing messages using RPC. The enums we use to maintain are in this file as well.
```python
class NodeECState(Enum):
    PARTICIPANT = 1
    NON_PARTICIPANT = 2	
    LEADER = 3		#node state for a process who is the leader
    
class MsgType(Enum):
    ACK = 1			#used for totally ordered multicast
    DATA = 2		#used for general data
    STATE = 3		#used to indicate state change info
    ELECTION = 4	#used for ring election algorithm
    LEADER = 5 		#used for ring election algorithm
```
6. The main implementation for the ring leader election is contained in `electionprocess.py`
7. The main implementation for the totally ordered multicast is contained in `logicalprocess.py`
8. The main implementation for the berkeley algorithm real clock synchronization is contianed in `realprocess.py`
9. `db.txt` which contains persistent storage and where all state change evnets are logged by the backend gateway. It also contains important messages and alerts like user enters house, alarm ring etc. When runned remotely on different machines this file will be located on the node of the backend gateway
10. `read_db.py` present in the `test` directory is a util file to process the logs generated in the `db.txt`
