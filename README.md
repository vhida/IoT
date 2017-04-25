## How to run

1. Open a terminal where we would run the name server. Since we use custom classes for message passing, the serializer needs to be mentioned to the name server. This can be done by issuing the command  
`export PYRO_SERIALIZERS_ACCEPTED=serpent,json,marshal,pickle`

2. Now we can start the python nameserver `python3 -m Pyro4.naming --host=<Host_IPaddr>`

3. Start the `gatewayback.py` backend db process
4. Start the `gatewayfront.py` frontend process
5. Start the various sensors and devices
6. Run the various test from the test folder

*Note:*
 - Please start the proceses in the above order as frontend talks to backend and other devices talk to the frontend gateway
 - To start any of the devices `x_device.py` or sensor `x_sensor.py` or frontend and backend gateway we run the command
   `python3 x_device.py ns_name:ns_port`  
    where ns_name and ns_port correspond to the name server host name and port number
 - Similarly, to run any test script from the tes directory issue the command `python3 <test_file>.py ns_name:ns_port`
 - This has been tested on Pyro4 and python3. The plots are generated using `ipython`, `matplotlib` and `pylab`

## Files

- A description of all the source files and code is given [here](docs/SourceFileDescriptions.md)
- A description of all the test files and code is give [here](docs/TestFileDescriptions.md)
- Some additional assumptions made are [here](docs/Assumption.md)

