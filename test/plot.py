import matplotlib.pyplot as plt
import pylab
import numpy as np
<<<<<<< HEAD
events = ['DELIVERED OPEN', 'DELIVERED KEY','DELIVERED YES', 'DELIVERED CLOSED', 'DELIVERED NO']
time = [159,161,162,164,166]
=======
events = ['RCVD OPEN', 'DELIVERED OPEN', 'RCVD KEY', 'DELIVERED KEY', 'RCVD YES', 'DELIVERED YES', 'RCVD CLOSED', 'DELIVERED CLOSED', 'RCVD NO', 'DELIVERED NO']
time = [3,4,8,9,11,12,16,17,19,20]
>>>>>>> cd5611465d975d7350de8f239e5d506c43997d3b
pylab.figure(1)

y = range(len(events))

pylab.yticks(y, events)

plt.plot(time, y, 'ro')
plt.xticks(np.arange(min(time), max(time)+1, 2))
plt.xlabel("time")
plt.ylabel("events")
plt.show()