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
# import the module that initiates and starts the gateway. ** DO NOT CHANGE THIS **
import mqttgateway.start_gateway as start_g

# import the module representing the interface ** CHANGE TO YOUR IMPORT HERE **
import mqttgateway.dummy_interface as dummy_i

PACKAGE_NAME = 'dummy2mqtt' # the actual name of this python package
# ** HERE THE PACKAGE IS THE SAME AS THE LIBRARY, SO IT IS NOT 'dummy2mqtt' BUT YOUR PACKAGE
#    WILL BE DIFFERENT AND HAS TO BE ENTERED HERE. ** 
APP_NAME = PACKAGE_NAME # ** GIVE YOUR APPLICATION A NAME **
# The application name can be anything, but the same name as the package is clearer

def main():
    ''' The entry point for the application '''

    # Initialise the application properties. ** NO NEED TO CHANGE ANYTHING HERE **
    AppProperties(__file__, app_name=APP_NAME)

    # Register the mqttgateway logger to use the library handlers.
    # ** KEEP THIS IF YOU WANT THE LOGS FROM THE LIBRARY IN YOUR APPLICATION **
    AppProperties().register_logger(logging.getLogger('mqttgateway'))

    # Register your own package logger to use the library handlers.
    # ** HERE IT IS NOT NEEDED BECAUSE WE ARE IN THE SAME PACKAGE BUT FOR YOUR APPLICATION
    #    YOU HAVE TO ADD IT BECAUSE YOUR CODE WILL BE IN A SEPARATE PACKAGE **
    #AppProperties().register_logger(logging.getLogger(PACKAGE_NAME))

    # launch the gateway ** CHANGE TO YOUR CLASS CALL HERE **
    start_g.startgateway(dummy_i.dummyInterface)

if __name__ == '__main__':
    main()
