''' This is a child class of the MQTT client class of the PAHO library.

.. Reviewed 20jun22

It includes the management of reconnection when using only the ``loop()`` method,
which is not included natively in the PAHO library as of 2018.

Notes on MQTT behaviour:

- if not connected, the ``loop`` and ``publish`` methods will not do anything,
  but raise no errors either.
- the ``loop`` method handles always only one message per call.

TODO: Review callbacks arguments types.
'''

import logging
import time
import paho.mqtt.client as mqtt

from mqttgateway import ENCODING
from mqttgateway.mqtt_map import internalMsg

LOG = logging.getLogger(__name__)

_MQTT_RC = { # Response codes
    0: 'Connection successful',
    1: 'Connection refused - incorrect protocol version',
    2: 'Connection refused - invalid client identifier',
    3: 'Connection refused - server unavailable',
    4: 'Connection refused - bad username or password',
    5: 'Connection refused - not authorised'
       # 6-255: Currently unused.
    }

_THROTTLELAG = 60  # lag in seconds to throttle the error logs.
_RACELAG = 0.5 # lag in seconds to wait before testing the connection state

class mgClient(mqtt.Client):
    ''' Class representing the MQTT connection. ``mg`` means ``MqttGateway``.

    Inheritance issues:
      The MQTT paho library sets quite a few attributes in the Client class.
      They all start with an underscore and have *standard* names (``_host``, ``_port``,...).
      Also, some high level methods are used extensively in the paho library itself,
      in particular the ``connect()`` method.  Overriding them is dangerous.
      That is why all the homonymous attributes and methods here have an ``mg_``
      prepended to avoid these problems.

    Args:
        host (string): a valid host address for the MQTT broker (excluding port)
        port (int): a valid port for the MQTT broker
        keepalive (int): see PAHO documentation
        client_id (string): the name (usually the application name) to send to the MQTT broker
        on_msg_func (function): function to call during on_message()
        topics (list of strings): e.g.['home/audiovideo/#', 'home/lighting/#']
        userdata (object): any object that will be passed to the call-backs
    '''

    def __init__(self, host: str='localhost', port: int=1883, keepalive: int=60,
                 client_id: str='', on_msg_func: callable=None,
                 topics: list=None, userdata: any=None):
        self._mg_host = host
        self._mg_port = port
        self._mg_keepalive = keepalive
        self._mg_client_id = client_id
        if on_msg_func is None: self.on_msg_func = lambda x: None
        else: self.on_msg_func = on_msg_func
        if topics is None: topics = []
        self.mg_topics = [] # list of tuples (topic, qos)
        for topic in topics:
            self.mg_topics.append((topic, 0))
        self._mg_userdata = {}
        self._mg_userdata['mgClient'] = self
        self._mg_userdata['userdata'] = userdata # even if it is None, at least the key exists
        self.mg_connected = False

        self._mg_connect_time = 0 # time of connection request
        self.lag_test = self.lag_end # lag_test is a 'function attribute', like a method.

        super().__init__(client_id=client_id, clean_session=True,
                         userdata=self._mg_userdata, protocol=mqtt.MQTTv311,
                         transport='tcp')
        self.on_connect = _on_connect
        self.on_disconnect = _on_disconnect
        self.on_message = _on_message
        self.on_subscribe = _on_subscribe
        # set up timer for the reconnect logs - see method below
        self.log_timer = None
        return

    def lag_end(self) -> bool:
        ''' Method to inhibit the connection test during the lag.

        One of the feature added by this class over the standard PAHO class is the
        possibility to reconnect when disconnected while using only the ``loop()`` method.
        In order to achieve this, the connection is checked regularly.
        At the very beginning of the connection though, there is the possibility of a race
        condition when testing the connection state too soon after requesting it.
        This happens if the ``on_connect`` call-back is not called
        fast enough by the PAHO library and the main loop tests the connection state
        before that call-back has had the time to set the state to ``connected``.
        As a consequence the automatic reconnection feature gets triggered
        while a connection is already under way, and the connection process gets jammed
        with the broker.
        That's why we need to leave a little lag before testing the connection.
        This is done with the function variable ``lag_test``, which is assigned to
        this function (``lag_end``) at connection, and switched to a *dummy* lambda
        after the lag has passed.
        '''
        if time.time() - self._mg_connect_time > _RACELAG:
            self.lag_test = lambda: True
            return True
        return False

    def lag_reset(self):
        ''' Resets the lag feature for a new connection request.'''
        self._mg_connect_time = time.time()
        self.lag_test = self.lag_end
        return

    def mg_connect(self):
        ''' Sets up the *lag* feature on top of the parent ``connect`` method.

        See :py:mod:`lag_end` for more information on the *lag feature*.
        '''
        LOG.debug('Attempt connection to host: <%s>, port: <%s>, keepalive: <%s>',
                  self._mg_host, self._mg_port, self._mg_keepalive)
        try:
            super().connect(self._mg_host, self._mg_port, self._mg_keepalive)
        except (OSError, IOError) as err:
            # the loop will try to reconnect anyway so just log an info
            LOG.info('Client can not connect to broker with error %s', err)
        # reset the 'lag' in any case, no point asking to reconnect straight away if it failed
        self.lag_reset()
        return

    def mg_reconnect(self):
        ''' Sets up the *lag* feature on top of the parent method.'''
        try:
            super().reconnect()
        except (OSError, IOError) as err:
            LOG.info('Client can not reconnect to broker with error %s', err)
        self.lag_reset()
        return

    def loop_with_reconnect(self, timeout):
        ''' Implements automatic reconnection on top of the parent loop method.

        The use of the method/attribute :py:meth:`lag_test` is to avoid having to test the
        lag forever once the connection is established.
        Once the lag is finished, this method gets replaced
        by a simple lambda, which hopefully is much faster than calling the time library and
        doing a comparison.
        '''
        if self.lag_test():
            if not self.mg_connected:
                try: self.mg_reconnect() # try to reconnect
                except (OSError, IOError): # still no connection
                    if self.log_timer is None or (time.monotonic() - self.log_timer > _THROTTLELAG):
                        LOG.warning('Client can not reconnect to broker.')
                        self.log_timer = time.monotonic()
        super().loop(timeout)

def mqttmsg_str(mqttmsg: internalMsg) -> str:
    ''' Returns a string representing the MQTT message object.

    As a reminder, the topic is unicode and the payload is binary.
    TODO: transfer this code to the class itself.
    '''
    return f"Topic: <{mqttmsg.topic}> - Payload: <{mqttmsg.payload.decode(ENCODING)}>."

def _on_connect(client: mgClient, userdata: any, # pylint: disable=unused-argument
                flags: dict, return_code: int):
    ''' The MQTT callback when a connection is established.

    It sets to True the ``connected`` attribute and subscribes to the
    topics available in the message map.

    As a reminder, the ``flags`` argument is a dictionary with at least
    the key ``session present`` (with a space!) which will be 1 if the session
    is already present.
    '''
    try: session_present = flags['session present']
    except KeyError: session_present = 'Info Not Available'
    LOG.debug('Session Present flag : %s', session_present)
    if return_code != 0: # failed
        LOG.warning('Connection failed with result code <%s>: %s',
                    return_code, _MQTT_RC[return_code])
        return
    LOG.info('Connected! Result message: %s', _MQTT_RC[return_code])
    client.mg_connected = True
    try:
        (result, mid) = client.subscribe(client.mg_topics)
    except ValueError as err:
        LOG.warning('Topic subscription <%s> error: %s', client.mg_topics, err)
    else:
        if result == mqtt.MQTT_ERR_NO_CONN:
            LOG.warning('Attempt to subscribe without connection.')
        elif result != mqtt.MQTT_ERR_SUCCESS:
            LOG.warning('Unrecognised result <%s> during subscription.', result)
        else:
            LOG.info('Message id <%s>: subscriptions successful to (topics, qos): %s',
                     mid, client.mg_topics)
    return

def _on_subscribe(client: mgClient, userdata: any, # pylint: disable=unused-argument
                  mid: str, granted_qos: list):
    ''' The MQTT callback when a subscription is completed.

    Only implemented for debug purposes.
    '''
    LOG.debug('Subscription id <%s> with (list of) qos %s', mid, granted_qos)
    return

def _on_disconnect(client: mgClient, userdata: any, # pylint: disable=unused-argument
                   return_code: int):
    ''' The MQTT callback when a disconnection occurs.

    It sets to False the ``mg_connected`` attribute.
    '''
    LOG.info('Client has disconnected with code <%s>.', return_code)
    client.mg_connected = False
    return

def _on_message(client: mgClient, userdata: any, # pylint: disable=unused-argument
                mqtt_msg: internalMsg):
    ''' The MQTT callback when a message is received from the MQTT broker.

    The message (topic and payload) is mapped into its internal representation and
    then appended to the incoming message list for the gateway interface to
    execute it later.
    '''
    LOG.debug('MQTT message received: %s', mqttmsg_str(mqtt_msg))
    userdata['mgClient'].on_msg_func(mqtt_msg)
    return
