'''
Launcher script for the **dummy** gateway.

Use this as a template.
If the name conventions have been respected, just change all occurrences of
``dummy`` into the name of your gateway.
'''

import os.path

import mqttgateway.utils.app_properties as app
app.Properties.init(os.path.realpath(__file__))

# import the module that initiates and starts the gateway
import mqttgateway.gateway.start_gateway as start_g

# import the module representing the interface *** change to your import here ***
import mqttgateway.dummy.dummy_interface as dummy_i

def main():
    # launch the gateway *** change to your class here ***
    start_g.startgateway(dummy_i.dummyInterface)

if __name__ == '__main__':
    main()