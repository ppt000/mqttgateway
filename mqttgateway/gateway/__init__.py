'''
.. reviewed 29May2018

The package representing the *core* of the application.

There are 4 modules:

- :py:mod:`mqtt_client` defines the child class of the official MQTT
  Client class of the paho library;
- :mod:`mqtt_map.py` defines the classes :class:`internalMsg` and :class:`msgMap`;
- :mod:`start_gateway.py` which contains the script for the
  application initialisation and main loop.
- :mod:`configuration.py` which contains the default configuration as a string.


This package uses the logger help provided by :mod:`mqttgateway.utils.app_properties`.
The :data:`Properties` object should have been already initialised by the application
using this library.
However, if that is not the case, the initialisation is done here with default parameters.
As a consequence, the main application should initialise :data:`Properties` before
importing anything from this package.
'''


import os.path
import mqttgateway.utils.app_properties as app
app.Properties.init(app_path=os.path.realpath(__file__), app_name='mqttgateway')