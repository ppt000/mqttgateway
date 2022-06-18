''' Defines the function that starts the gateway.

.. Reviewed 11 November 2018.
'''

import traceback
import threading
import logging

import mqttgateway.mqtt_client as mqtt
import mqttgateway.mqtt_map as mqtt_map
from mqttgateway.app_properties import AppProperties
from mqttgateway import __version__

LOG = logging.getLogger(__name__)

def startgateway(gateway_interface):
    ''' Entry point.'''
    #AppProperties(app_path=__file__, app_name='mqttgateway') # does nothing if already been called
    try:
        _startgateway(gateway_interface)
    except:
        LOG.error(''.join(('Fatal error: ', traceback.format_exc())))
        raise

def _startgateway(gateway_interface):
    '''
    Initialisation of the application and main loop.

    Initialises the configuration and the log, starts the interface,
    starts the MQTT communication then starts the main loop.
    The loop can start in mono or multi threading mode.
    If the ``loop`` method is defined in the ``gateway_interface`` class, then
    the loop will operate in a single thread, and this function will actually *loop*
    forever, calling every time the ``loop`` method of the interface, as well
    as the ``loop`` method of the MQTT library.
    If the ``loop`` method is not defined in the ``gateway_interface`` class, then
    it is assumed that the ``loop_start`` method is defined and it will be launched in a
    separate thread.
    The priority given to the mono thread option is for backward compatibility.

    The data files are:

    - the configuration file (compulsory), which is necessary at least to define
      the MQTT broker; a path to it can be provided as first argument of the command line,
      or the default path will be used;
    - the map file (optional), if the mapping option is enabled.

    The rules for providing paths of files are available in the configuration file
    template as a comment.
    The same rules apply to the command line argument and to the paths provided in the
    configuration file.

    Args:
        gateway_interface (class): the interface class (not an instance of it!)
    '''

    # Load the configuration ======================================================================
    cfg = AppProperties().config

    # Log the configuration used ==================================================================
    LOG.info('=== APPLICATION STARTED ===')
    LOG.info(''.join(('mqttgateway version: <', __version__, '>.')))
    LOG.info('Configuration options used:')
    for section in cfg.sections():
        for option in cfg.options(section):
            LOG.info(''.join(('   [', section, '].', option, ' : <',
                              str(cfg.get(section, option)), '>.')))
    # Exit in case of error processing the configuration file.
    if cfg.has_section('CONFIG') and cfg.has_option('CONFIG', 'error'):
        LOG.critical(''.join(('Error while processing the configuration file:\n\t',
                              cfg.get('CONFIG', 'error'))))
        raise SystemExit

    # Instantiate the gateway interface ===========================================================
    # Create the dictionary of the parameters for the interface from the configuration file
    interfaceparams = {} # Collect the interface parameters from the configuration, if any
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
        try:
            map_data = AppProperties().get_jsonfile(mapfilename, extension='.map')
        except (OSError, IOError) as err:
            LOG.critical(''.join(('Error loading map file:/n/t', str(err))))
            raise SystemExit
        except ValueError as err:
            LOG.critical(''.join(('Error reading JSON file:/n/t', str(err))))
            raise SystemExit
    else: # use default map - take root and topics from configuration file
        mqtt_map.NO_MAP['root'] = cfg.get('MQTT', 'root')
        mqtt_map.NO_MAP['topics'] = [topic.strip() for topic in cfg.get('MQTT', 'topics').split(',')]
        map_data = None
    try:
        messagemap = mqtt_map.msgMap(map_data) # will raise ValueErrors if problems
    except ValueError as err:
        LOG.critical(''.join(('Error processing map file:/n/t', str(err))))

    # Initialise the MQTT client and connect ======================================================

    def process_mqttmsg(mqtt_msg):
        ''' Converts a MQTT message into an internal message and pushes it on the message list.

        This function will be called by the on_message MQTT call-back.
        Placing it here avoids passing the ``messagemap`` and the ``msglist_in`` instances
        but do not prevent the danger of messing up a multi-threading application.
        Here if the messagemap is not changed during the application's life (and for now
        this is not a feature), it should be fine.

        Args:
            mqtt_msg (:class:`mqtt.Message`): incoming MQTT message.
        '''
        # TODO: Make sure this works in various cases during multi-threading.
        try: internal_msg = messagemap.mqtt2internal(mqtt_msg)
        except ValueError as err:
            LOG.info(str(err))
            return
        # eliminate echo
        if internal_msg.sender != messagemap.sender():
            msglist_in.push(internal_msg)
        return

    timeout = cfg.getfloat('MQTT', 'timeout') # for the MQTT loop() method
    client_id = cfg.get('MQTT', 'clientid')
    if not client_id: client_id = AppProperties().name
    mqttclient = mqtt.mgClient(host=cfg.get('MQTT', 'host'),
                               port=cfg.getint('MQTT', 'port'),
                               keepalive=cfg.getint('MQTT', 'keepalive'),
                               client_id=client_id,
                               on_msg_func=process_mqttmsg,
                               topics=messagemap.topics)
    mqttclient.mg_connect()

    def publish_msglist(block=False, timeout=None):
        ''' Publishes all messages in the outgoing message list.'''
        while True: # Publish the messages returned, if any.
            internal_msg = msglist_out.pull(block, timeout)
            if internal_msg is None: break # should never happen in blocking mode
            try: mqtt_msg = messagemap.internal2mqtt(internal_msg)
            except ValueError as err:
                LOG.info(str(err))
                continue
            published = mqttclient.publish(mqtt_msg.topic, mqtt_msg.payload, qos=0, retain=False)
            LOG.debug(''.join(('MQTT message published with (rc, mid): ', str(published),
                               '\n\t', mqtt.mqttmsg_str(mqtt_msg))))
        return

    # 2018-10-19 Add code to provide multi threading support
    if hasattr(gatewayinterface, 'loop') and callable(gatewayinterface.loop):
        LOG.info('Mono Thread Loop')
        while True:
            mqttclient.loop_with_reconnect(timeout) # Call the MQTT loop.
            gatewayinterface.loop() # Call the interface loop.
            publish_msglist(block=False, timeout=None)
    else: # assume 'loop_start' is defined and use multi-threading
        LOG.info('Multi Thread Loop')
        publisher = threading.Thread(target=publish_msglist, name='Publisher',
                                     kwargs={'block': True, 'timeout': None})
        publisher.start()
        mqttclient.loop_start() # Call the MQTT loop.
        gatewayinterface.loop_start() # Call the interface loop.
        block = threading.Event()
        block.wait() # wait forever - TODO: implement graceful termination
