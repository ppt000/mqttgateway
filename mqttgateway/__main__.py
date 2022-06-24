'''
Launcher script for the **dummy** gateway.

.. REVIEWED 21jun22

This is an *empty* gateway to test the installation setup.
It allows to test the loading of the configuration files,
the log setup and the basic operation of the core application.

One can also use this as a template.
If the name conventions have been respected, just change all occurrences of
``dummy`` into the name of your interface.

'''

from configparser import ConfigParser
import json
from pathlib import Path
import importlib.resources as res
import random
import string

from mqttgateway import ENCODING
# import the class for all the application properties. **DO NOT CHANGE THIS **
from mqttgateway.app_config import AppConfig
# import the module that initiates and starts the gateway. ** DO NOT CHANGE THIS **
from mqttgateway.start_gateway import startgateway

# import the module representing the interface ** CHANGE TO YOUR IMPORT HERE **
from mqttgateway.dummy_interface import dummyInterface

PACKAGE_NAME = 'dummy2mqtt' # the actual name of this python package
# ** HERE THE PACKAGE IS THE SAME AS THE LIBRARY, SO IT IS NOT 'dummy2mqtt' BUT YOUR PACKAGE
#    WILL BE DIFFERENT AND HAS TO BE ENTERED HERE. **
APP_NAME = PACKAGE_NAME # ** GIVE YOUR APPLICATION A NAME **
# The application name can be anything, but the same name as the package is clearer

def main():
    ''' The entry point for the application '''

    # locate the resources folder within this project
    #res_dir = Path( Path(__file__).parent, 'res')

    # retrieve the demo configuration file
    cfg = ConfigParser()

    #result = cfg.read(Path(res_dir, 'dummy2mqtt.cfg'), encoding=ENCODING)
    #if len(result) != 1:
    #    raise FileNotFoundError("Could not find configuration"
    #                            f" file {Path(res_dir, 'dummy2mqtt.cfg')}")

    cfg.read_string(res.read_text('mqttgateway.res', 'dummy2mqtt.cfg'))

    # retrieve the mappingf for the dummy interface
    # what follows could raise FileNotFoundError or json.JSONDecodeError
    #with open(Path(res_dir, 'dummy_map.json'), mode='rt', encoding=ENCODING) as infile:
    with res.open_text('mqttgateway.res', 'dummy_map.json', encoding=ENCODING) as infile:
        map_data = json.load(infile)
    # add a random string to the root of the topic in case a public test broker is used
    #map_data['root'] +=  '_' + ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    # TODO: implement change of root with automatic change of topics to subscribe to.

    # Initialise the application properties. ** NO NEED TO CHANGE ANYTHING HERE **
    AppConfig.init(app_name=APP_NAME, cfg=cfg, map_data=map_data)

    # Register your own package logger to use the library handlers.
    # ** HERE IT IS NOT NEEDED BECAUSE WE ARE IN THE SAME PACKAGE BUT FOR YOUR APPLICATION
    #    YOU HAVE TO ADD IT BECAUSE YOUR CODE WILL BE IN A SEPARATE PACKAGE **
    #AppConfig.add_handlers(logging.getLogger(YOUR_PACKAGE_NAME))

    # launch the gateway ** CHANGE TO YOUR CLASS CALL HERE **
    startgateway(dummyInterface)

if __name__ == '__main__':
    main()
