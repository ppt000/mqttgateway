'''
Defines the function that starts the gateway and the 3 MQTT callbacks.

This module exposes the main entry points for the framework: the gateway
interface class, which is received as an argument by the main function
:func:`startgateway`, and is instantiated after all the initialisations are
done. Note that at the moment of instantiation, the configuration file should be
loaded, so anything that is written inside the ``[INTERFACE]`` section will be passed
on to the class constructor.  This way custom configuration settings can be passed
on to the gateway interface.

.. TODO
    Move the MQTT callbacks in a different module inside a class?
    Remove definitively all commented lines relating to reconnection attempts
'''

import sys
import json

import mqttgateway.gateway.mqtt_client as mqtt
import mqttgateway.utils.app_properties as app
import mqttgateway.gateway.mqtt_map as mqtt_map

from mqttgateway.utils.load_config import loadconfig
from mqttgateway.utils.init_logger import initlogger

from mqttgateway.gateway.configuration import CONFIG

def startgateway(gateway_interface):
    '''
    Initialisation and main loop.

    Initialises the configuration and the logger, starts the interface,
    starts the MQTT communication then starts the main loop.
    The loop calls the MQTT loop method to process any message from the broker,
    then calls the gateway interface loop, and finally publishes all MQTT
    messages queued.

    Notes on MQTT behaviour:

    - if not connected, the `loop` and `publish` methods will not do anything,
      but raise no errors either.
    - it seems that the `loop` method handles always only one message per call.

    Notes on the loading of data:
    the configuration file is the only file that needs to be either
    passed as argument through the command line, or the default settings will
    be used (and probably fail as one needs at least a valid MQTT broker for
    the application to start).  All other filenames will be in the configuration
    file itself. The configuration file name can be passed as the first argument
    in the command line.  If the argument is a directory (i.err. ends with a slash)
    then it is appended with the default file name. If it is a path it is checked
    to see if it is absolute, and if it is not it will be prepended with the path
    of the calling script.  The default file name is the name of the calling script
    with the ``.conf`` extension.  The default directory is the directory of
    the calling script.

    Args:
        gateway_interface (class (not an instance of it!)): the interface
            The only requirement is that it should have an appropriate constructor
            and a ``loop`` method.

    Raises:
        OSError: if any of the necessary files are not found.

            The necessary files are the configuration file (which is necessary to define
            the MQTT broker, at the very least) and the map (for which there can not be
            any default).
            It tries to catch most other 'possible' exceptions.
            KeyboardInterrupt should work as there are a few pauses around. Finally,
            only errors thrown by the provided interface class will not be caught and
            could terminate the application.
    '''

    # Load the configuration. Check the first command line argument for the filename.
    cfg = loadconfig(CONFIG, app.Properties.config_file_path)

    # Initialise the logger handlers
    logfilename = cfg.get('LOG', 'logfilename')
    if not logfilename: logfilepath = None
    else: logfilepath = app.Properties.get_path('.log', logfilename)
    logfiledata = (logfilepath, cfg.getboolean('LOG', 'debug'), cfg.get('LOG', 'consolelevel'))
    emaildata = (cfg.get('LOG', 'emailhost'), cfg.get('LOG', 'emailport'),
                 cfg.get('LOG', 'emailaddress'), app.Properties.name)
    initlogger(app.Properties.root_logger, logfiledata, emaildata)
    logger = app.Properties.get_logger(__name__)

    # Log the configuration used.
    logger.info('=== APPLICATION STARTED ===')
    logger.info('Configuration:')
    for section in cfg.sections():
        for option in cfg.options(section):
            logger.info(''.join(('   [', section, '].', option, ' : <',
                                 str(cfg.get(section, option)), '>.')))

    # Warn in case of error processing the configuration file.
    if cfg.has_section('CONFIG') and cfg.has_option('CONFIG', 'error'):
        logger.critical(''.join(('Error while processing the configuration file:\n\t',
                                 cfg.get('CONFIG', 'error'), '\n ABORT!')))
        raise SystemExit

    # Create 2 message lists, one incoming, the other outgoing
    msglist_in = mqtt_map.MsgList()
    msglist_out = mqtt_map.MsgList()

    # Instantiate the gateway interface.
    interfaceparams = {} # the parameters for the interface from the configuration file
    for option in cfg.options('INTERFACE'): # read the configuration parameters in a dictionary
        interfaceparams[option] = str(cfg.get('INTERFACE', option))
    gatewayinterface = gateway_interface(interfaceparams, msglist_in, msglist_out)

    # Load the map data.
    mapping_flag = cfg.getboolean('MQTT', 'mapping')
    mapfilename = cfg.get('MQTT', 'mapfilename')
    if mapping_flag and mapfilename:
        mapfilepath = app.Properties.get_path('.map', mapfilename)
        try:
            with open(mapfilepath, 'r') as mapfile:
                map_data = json.load(mapfile)
        except (OSError, IOError) as err:
            logger.critical(''.join(('Error <', str(err), '> with map file <', mapfilepath, '>.')))
            raise SystemExit
    else:
        mqtt_map.NO_MAP['root'] = cfg.get('MQTT', 'root')
        mqtt_map.NO_MAP['topics'] = [topic.strip() for topic in cfg.get('MQTT', 'topics').split(',')]
        map_data = None
    messagemap = mqtt_map.msgMap(map_data) # will raise ValueErrors if problems

    # Initialise the dictionary to store parameters and to pass to the callbacks
    timeout =  cfg.getfloat('MQTT', 'timeout') # for the MQTT loop() method

    #===============================================================================================
    # localdata = {}
    # localdata['timeout'] = cfg.getfloat('MQTT', 'timeout') # for the MQTT loop() method
    # localdata['msgmap'] = messagemap
    # localdata['msglist_in'] = msglist_in
    # localdata['interface'] = gatewayinterface
    #===============================================================================================

    # the function that will be called by the on_message MQTT call-back
    def process_mqttmsg(mqtt_msg):
        ''' docstring.'''
        try: internal_msg = messagemap.mqtt2internal(mqtt_msg)
        except ValueError as err:
            logger.info(str(err))
            return
        msglist_in.push(internal_msg)

    # Initialise the MQTT client and connect.
    client_id = cfg.get('MQTT', 'clientid')
    if not client_id: client_id = app.Properties.name
    mqttclient = mqtt.mgClient(host=cfg.get('MQTT', 'host'),
                               port=cfg.getint('MQTT', 'port'),
                               keepalive=cfg.getint('MQTT', 'keepalive'),
                               client_id=client_id,
                               on_msg_func=process_mqttmsg,
                               topics=messagemap.topics) #, userdata=localdata)

    # Main loop
    while True:

        # Call the MQTT loop.
        mqttclient.loop(timeout)

        # Call the interface loop.
        gatewayinterface.loop()

        # Publish the messages returned, if any.
        while True:
            internal_msg = msglist_out.pull()
            if internal_msg is None: break
            try: mqtt_msg = messagemap.internal2mqtt(internal_msg)
            except ValueError as err:
                logger.info(str(err))
                continue
            mqttclient.publish(mqtt_msg.topic, mqtt_msg.payload, qos=0, retain=False)
