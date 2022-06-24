''' Defines the function that starts the gateway.

.. Reviewed 18 June 2022
'''

import traceback
import threading
import logging
import time

import paho.mqtt.client as mqtt

from mqttgateway import mqtt_map, END_THREAD
from mqttgateway import mqtt_client
from mqttgateway.app_config import AppConfig

LOG = logging.getLogger(__name__)

def startgateway(gateway_interface):
    ''' Entry point.'''
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

    app = AppConfig()

    # Instantiate the gateway interface ===========================================================
    # Create the dictionary of the parameters for the interface from the configuration file
    interfaceparams = {} # Collect the interface parameters from the configuration, if any
    for option in app.config.options('INTERFACE'):
        interfaceparams[option] = str(app.config.get('INTERFACE', option))
    # Create 2 message lists, one incoming, the other outgoing
    msglist_in = mqtt_map.MsgList()
    msglist_out = mqtt_map.MsgList()
    gatewayinterface = gateway_interface(interfaceparams, msglist_in, msglist_out)

    if app.map_data is None: # use default map - take root and topics from configuration file
        map_data = {'root': app.config.get('MAP', 'root'),
                    'topics': [topic.strip() for topic in app.config.get('MAP', 'topics').split(',')]}
    else:
        map_data = app.map_data

    try:
        messagemap = mqtt_map.msgMap(map_data) # will raise ValueErrors if problems
    except ValueError as err:
        LOG.critical('Error processing map file:/n/t%s', err)

    # Initialise the MQTT client and connect ======================================================

    def process_mqttmsg(mqtt_msg: mqtt.MQTTMessage):
        ''' Converts a MQTT message into an internal message and pushes it on the message list.

        This function will be called by the on_message MQTT call-back.
        Placing it here avoids passing the ``messagemap`` and the ``msglist_in`` instances
        but do not prevent the danger of messing up a multi-threading application.
        Here if the messagemap is not changed during the application's life (and for now
        this is not a feature), it should be fine.

        Args:
            mqtt_msg (:class:`mqtt.MQTTMessage`): incoming MQTT message.
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

    timeout = app.config.getfloat('MQTT', 'timeout') # for the MQTT loop() method
    client_id = app.config.get('MAP', 'clientid')
    if not client_id: client_id = AppConfig().name
    mqttclient = mqtt_client.mgClient(host=app.config.get('MQTT', 'host'),
                               port=app.config.getint('MQTT', 'port'),
                               keepalive=app.config.getint('MQTT', 'keepalive'),
                               client_id=client_id,
                               on_msg_func=process_mqttmsg,
                               topics=messagemap.topics)
    mqttclient.mg_connect()

    def publish_msglist(block=False, timeout=None):
        ''' Publishes all messages in the outgoing message list.'''
        while True: # Publish the messages returned, if any.
            internal_msg = msglist_out.pull(block, timeout)
            if internal_msg is None: break # should never happen in blocking mode
            if internal_msg is END_THREAD:
                LOG.info('Terminating thread.')
                break
            try: mqtt_msg = messagemap.internal2mqtt(internal_msg)
            except ValueError as err:
                LOG.info(str(err))
                continue
            published = mqttclient.publish(mqtt_msg.topic, mqtt_msg.payload, qos=0, retain=False)
            LOG.debug(''.join(('MQTT message published with (rc, mid): ', str(published),
                               '\n\t', mqtt_client.mqttmsg_str(mqtt_msg))))
        return

    # check if 'loop_start' is defined and use multi-threading
    if hasattr(gatewayinterface, 'loop_start') and callable(gatewayinterface.loop_start):
        LOG.info('Multi Thread Loop')
        publisher = threading.Thread(target=publish_msglist, name='Publisher',
                                     kwargs={'block': True, 'timeout': None})
        publisher.start()
        mqttclient.loop_start() # Call the MQTT loop.
        gatewayinterface.loop_start() # Call the interface loop.
        block = threading.Event()
        try:
            while True:
                block.wait(timeout=5) # check KeyboardInterrupt periodically
        except KeyboardInterrupt:
            msglist_out.push(END_THREAD) # terminate the Publisher thread
            mqttclient.loop_stop() # terminate the MQTT client thread
            gatewayinterface.loop_stop() # terminate the interface thread(s)
            time.sleep(30) # wait for all threads to terminate?
            LOG.info('Terminating main thread.')
    else: # assume 'loop' is defined and use mono-threading
        LOG.info('Mono Thread Loop')
        while True:
            mqttclient.loop_with_reconnect(timeout) # Call the MQTT loop.
            gatewayinterface.loop() # Call the interface loop.
            publish_msglist(block=False, timeout=None)
