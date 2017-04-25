## Test

All the test files are in the test directory

1. `mult_msg.py`
Run this program to simulate a series of temperature changes in concurrent. Key test: all devices, sensors and gateway receive events in same order. 

2. `user_enter_exit.py`
Run this program to simulate a user entry and exit. Key test: correct ordering of events and inference at the gateway to turn security system on/off, system mode to home/away

3. `theif_enter.py`
Run this program to simulate a theif entering the hose. Key test: correct ordering of events and raise alarm

4. `pull_test.py`
Run this program to pull the current state of all devices and sensor at any instant of time. Key test: pull functionality of devices/sensors

5. `standalone_election_test.py`
Run this program to simulate a ring based leader election algorithm. Key test: it simulates test for both all nodes live as well as some nodes down. Reports leader as the max process PID

6. `talk_test.py`
Run this program to simulate a hypothetical scenario where various commands are sent to the devices and sensors. Key test: to ensure all events are recevied in the same order.

----
To run the test cases above:-
- In the file first change the desired mode of clock synchonrization to either `LOGICAL` or `REAL` in the variable `MODE`
- In addition for the file `talk_test.py` it expects a user input a sample of which is show in the file `inp.txt`
- The `inp.txt` expects the first line to be a number indicating the number of commands to be dispatched, the next N lines contains the command
- each command is the name of the device, sensor to be affected followed by a space followed by the state change or data for that device/sensor
