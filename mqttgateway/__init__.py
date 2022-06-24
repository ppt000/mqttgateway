''' The **mqttgateway** library helps in building gateways between connected devices and MQTT systems.

.. REVIEWED 10 November 2018

This package has 4 *groups* of files:

* the **core** of the library made of the modules:

   - :py:mod:`start_gateway.py <mqttgateway.start_gateway>` which contains the script for the
     application initialisation and main loop;
   - :py:mod:`mqtt_client.py <mqttgateway.mqtt_client>` which defines the child of the MQTT Client class
     of the paho library, needed to implement a few extra features;
   - :py:mod:`mqtt_map.py <mqttgateway.mqtt_map>` which defines the internal message class
     :py:class:`internalMsg <mqttgateway.mqtt_map.internalMsg>`
     and the mapping class :py:class:`msgMap <mqttgateway.mqtt_map.msgMap>`.

* the **utilities** used by the core and that are really *application agnostic*; these
  are in the modules:

   - :py:mod:`app_properties.py <mqttgateway.app_properties>`, a singleton that holds
     application wide data like name, directories where to look for files, configuration
     and log information;
   - :py:mod:`init_logger <mqttgateway.init_logger>`, used by ``app_properties`` to initialise
     the loggers and handlers;
   - :py:mod:`load_config <mqttgateway.load_config>`, used by ``app_properties`` to load the
     configuration;
   - :py:mod:`throttled_exception <mqttgateway.throttled_exception>`, an exception class that
     *mutes* events if they are too frequent, handy for connection problems happening in fast
     loops.

* the ``dummy`` interface, an empty interface to test the installation of the
  library and to be used as a template to write a new interface, and which is made of the
  modules:

   - :py:mod:`dummy_start <mqttgateway.dummy_start>`, the launcher script;
   - :py:mod:`dummy_interface <mqttgateway.dummy_interface>`, the actual interface main class.

* various data files:

   - ``default.conf``, the file containing all the configuration options and their default
      values;
   - ``mqtt_map_schema.json``, the schema of the mapping files;
   - ``dummy_map.json`` and ``dummy2mqtt.conf``, the map and configuration file of the
     ``dummy`` interface.

'''

VERSION = '2.0.0'

LIBRARY_NAME = 'mqttgateway'

ENCODING = 'utf-8'

END_THREAD = object()
