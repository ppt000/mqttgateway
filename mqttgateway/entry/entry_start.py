'''
Launcher script for the **entry** gateway.

.. reviewed 30 May 2018

'''

import os.path

_APP_NAME = 'entry2mqtt'

import mqttgateway.utils.app_properties as app
app.Properties.init(os.path.realpath(__file__), app_name=_APP_NAME)

# import the module that initiates and starts the gateway
import mqttgateway.gateway.start_gateway as start_g

# import the module representing the interface
import mqttgateway.entry.entry_interface as entry_i

def main():
    ''' launch the gateway'''
    start_g.startgateway(entry_i.entryInterface)

if __name__ == '__main__':
    main()
