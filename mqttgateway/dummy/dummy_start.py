''' Launcher script for the **dummy** interface.

.. reviewed 30 May 2018

Use this as a template.
If the name conventions have been respected, just change all occurrences of
``dummy`` into the name of your interface.
'''

import os.path

_APP_NAME = 'dummy2mqtt'

import mqttgateway.utils.app_properties as app
app.Properties.init(os.path.realpath(__file__), app_name=_APP_NAME)

# import the module that initiates and starts the gateway
import mqttgateway.gateway.start_gateway as start_g

# import the module representing the interface *** change to your import here ***
import mqttgateway.dummy.dummy_interface as dummy_i

def main():
    ''' The entry point for the application '''
    # launch the gateway *** change to your class here ***
    start_g.startgateway(dummy_i.dummyInterface)

if __name__ == '__main__':
    main()
