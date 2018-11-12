'''
Launcher script for the **dummy** gateway.

.. REVIEWED 11 November 2018

This is an *empty* gateway to test the installation setup.
It allows to test the loading of the configuration files,
the log setup and the basic operation of the core application.

One can also use this as a template.
If the name conventions have been respected, just change all occurrences of
``dummy`` into the name of your interface.

'''

import logging

# import the class for all the application properties. **DO NOT CHANGE THIS **
from mqttgateway.app_properties import AppProperties
# import the module that initiates and starts the gateway. **DO NOT CHANGE THIS **
import mqttgateway.start_gateway as start_g

# import the module representing the interface ** CHANGE TO YOUR IMPORT HERE **
import mqttgateway.dummy_interface as dummy_i

APP_NAME = 'dummy2mqtt' # Give your application a name.

def main():
    ''' The entry point for the application '''
    # Initialise the application properties. ** NO NEED TO CHANGE ANYTHING HERE **
    AppProperties(__file__, app_name=APP_NAME)
    # Register the package logger to use the mqttgateway handlers.
    # ** KEEP THIS IF YOU WANT THE LOGS FROM THE LIBRARY IN YOUR APPLCATION **
    AppProperties().register_logger(logging.getLogger('mqttgateway'))
    # launch the gateway ** CHANGE TO YOUR CLASS CALL HERE **
    start_g.startgateway(dummy_i.dummyInterface)

if __name__ == '__main__':
    main()
