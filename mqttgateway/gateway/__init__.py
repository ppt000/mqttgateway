'''
The package representing the *core* of the application.

There are 4 modules:

- :mod:`mqtt_client.py` defines the child class of the official MQTT
  Client class of the paho library;
- :mod:`mqtt_map.py` defines the classes :class:`internalMsg` and
  :class:`msgMap`;
- :mod:`start_gateway.py` which contains the script for the
  application initialisation and main loop.
- :mod:`configuration.py` which contains the default configuration as a string.
'''
