'''
Launcher script for the **entry** gateway.

.. REVIEWED 27 October 2018

'''

import logging

# import the module that initiates and starts the gateway
import mqttgateway.gateway.start_gateway as start_g

# import the module representing the interface
import mqttgateway.entry.entry_interface as entry_i

from mqttgateway.utils.app_properties import AppProperties

_APP_NAME = 'entry2mqtt'

def main():
    ''' launch the gateway'''
    # Initialise the application properties
    AppProperties(__file__, app_name=_APP_NAME)
    # Register the package logger to use the mqttgateway handlers.
    AppProperties().register_logger(logging.getLogger(__package__))
    start_g.startgateway(entry_i.entryInterface)

if __name__ == '__main__':
    main()
