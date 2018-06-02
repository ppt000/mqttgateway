''' Defines the function that starts the gateway.

.. Reviewed 30 May 2018.
'''

import json
import traceback

import mqttgateway.gateway.mqtt_client as mqtt
import mqttgateway.utils.app_properties as app
import mqttgateway.gateway.mqtt_map as mqtt_map

from mqttgateway.utils.load_config import loadconfig
from mqttgateway.utils.init_logger import initlogger

from mqttgateway.gateway.configuration import CONFIG

_logger = app.Properties.get_logger(__name__)

def startgateway(gateway_interface):
    ''' Entry point.'''
    try:
        _startgateway(gateway_interface)
    except:
        _logger.error(''.join(('Fatal error: ', traceback.format_exc())))
        raise

def _startgateway(gateway_interface):
    '''
    Initialisation of the application and main loop.

    Initialises the configuration and the logger, starts the interface,
    starts the MQTT communication then starts the main loop.

    The data files are:

    - the configuration file (compulsory), which is necessary at least to define the MQTT broker;
      a path to it can be provided as first argument of the command line, or the default path
      will be used;
    - the map file (optional), if the mapping option is enabled.

    The rules for providing paths of files are available in the configuration file template as
    a comment. The same rules apply to the command line argument and to the paths provided in the
    configuration file.

    Args:
        gateway_interface (class (not an instance of it!)): the interface class
    '''

    # Load the configuration ======================================================================
    cfg = loadconfig(CONFIG, app.Properties.config_file_path)

    # Initialise the logger handlers ==============================================================
    logfilename = cfg.get('LOG', 'logfilename')
    if not logfilename: logfilepath = None
    else: logfilepath = app.Properties.get_path('.log', logfilename)
    # create the tuple to send the arguments to initlogger
    logfiledata = (logfilepath, cfg.getboolean('LOG', 'debug'), cfg.get('LOG', 'consolelevel'))
    emaildata = (cfg.get('LOG', 'emailhost'), cfg.get('LOG', 'emailport'),
                 cfg.get('LOG', 'emailaddress'), app.Properties.name)
    initlogger(app.Properties.root_logger, logfiledata, emaildata)
    #logger = app.Properties.get_logger(__name__)

    # Log the configuration used ==================================================================
    _logger.info('=== APPLICATION STARTED ===')
    _logger.info('Configuration:')
    for section in cfg.sections():
        for option in cfg.options(section):
            _logger.info(''.join(('   [', section, '].', option, ' : <',
                                 str(cfg.get(section, option)), '>.')))

    # Exit in case of error processing the configuration file.
    if cfg.has_section('CONFIG') and cfg.has_option('CONFIG', 'error'):
        _logger.critical(''.join(('Error while processing the configuration file:\n\t',
                                 cfg.get('CONFIG', 'error'))))
        raise SystemExit

    # Instantiate the gateway interface ===========================================================
    # Create the dictionary of the parameters for the interface from the configuration file
    interfaceparams = {}
    for option in cfg.options('INTERFACE'):
        interfaceparams[option] = str(cfg.get('INTERFACE', option))
    # Create 2 message lists, one incoming, the other outgoing
    msglist_in = mqtt_map.MsgList()
    msglist_out = mqtt_map.MsgList()
    gatewayinterface = gateway_interface(interfaceparams, msglist_in, msglist_out)

    # Load the map data ===========================================================================
    mapping_flag = cfg.getboolean('MQTT', 'mapping')
    mapfilename = cfg.get('MQTT', 'mapfilename')
    if mapping_flag and mapfilename:
        mapfilepath = app.Properties.get_path('.map', mapfilename)
        try:
            with open(mapfilepath, 'r') as mapfile:
                map_data = json.load(mapfile)
        except (OSError, IOError) as err:
            _logger.critical(''.join(('Error loading map file <', mapfilepath, '>:/n/t', str(err))))
            raise SystemExit
    else: # use default map - take root and topics from configuration file
        mqtt_map.NO_MAP['root'] = cfg.get('MQTT', 'root')
        mqtt_map.NO_MAP['topics'] = [topic.strip() for topic in cfg.get('MQTT', 'topics').split(',')]
        map_data = None
    try: messagemap = mqtt_map.msgMap(map_data) # will raise ValueErrors if problems
    except ValueError as err:
        _logger.critical(''.join(('Error processing map file <', mapfilepath, '>:/n/t', str(err))))

    # Initialise the MQTT client and connect ======================================================
    # Define the function that will be called by the on_message MQTT call-back
    def process_mqttmsg(mqtt_msg):
        ''' Converts a MQTT message into an internal message and pushes it on the message list.

        Args:
            mqtt_msg (:class:`mqtt.Message`): incoming MQTT message.
        '''
        try: internal_msg = messagemap.mqtt2internal(mqtt_msg)
        except ValueError as err:
            _logger.info(str(err))
            return
        msglist_in.push(internal_msg)
        return

    timeout = cfg.getfloat('MQTT', 'timeout') # for the MQTT loop() method
    client_id = cfg.get('MQTT', 'clientid')
    if not client_id: client_id = app.Properties.name
    mqttclient = mqtt.mgClient(host=cfg.get('MQTT', 'host'),
                               port=cfg.getint('MQTT', 'port'),
                               keepalive=cfg.getint('MQTT', 'keepalive'),
                               client_id=client_id,
                               on_msg_func=process_mqttmsg,
                               topics=messagemap.topics)

    # Main loop ===================================================================================
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
                _logger.info(str(err))
                continue
            mqttclient.publish(mqtt_msg.topic, mqtt_msg.payload, qos=0, retain=False)
