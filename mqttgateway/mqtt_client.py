''' This is a child class of the MQTT client class of the PAHO library.

.. Reviewed 11 November 2018.

It includes the management of reconnection when using only the ``loop()`` method,
which is not included natively in the current PAHO library.

Notes on MQTT behaviour:

- if not connected, the ``loop`` and ``publish`` methods will not do anything,
  but raise no errors either.
- the ``loop`` method handles always only one message per call.

'''

import logging
import time
import paho.mqtt.client as mqtt

import mqttgateway.throttled_exception as thrx
from mqttgateway import ENCODING

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

_THROTTLELAG = 600  # lag in seconds to throttle the error logs.
_RACELAG = 0.5 # lag in seconds to wait before testing the connection state

class connectionError(thrx.ThrottledException):
    # pylint: disable=too-few-public-methods
    ''' Base Exception class for this module, inherits from ThrottledException'''
    # pylint: enable=too-few-public-methods
    def __init__(self, msg=None):
        super(connectionError, self).__init__(msg, throttlelag=_THROTTLELAG, module_name=__name__)

# pylint: disable=unused-argument

def mqttmsg_str(mqttmsg):
    ''' Returns a string representing the MQTT message object.
    
    As a reminder, the topic is unicode and the payload is binary.
    '''
    return ''.join(('Topic: <', mqttmsg.topic,
                    '> - Payload: <', mqttmsg.payload.decode(ENCODING), '>.'))

def _on_connect(client, userdata, flags, return_code):
    ''' The MQTT callback when a connection is established.

    It sets to True the ``connected`` attribute and subscribes to the
    topics available in the message map.

    As a reminder, the ``flags`` argument is a dictionary with at least
    the key ``session present`` (with a space!) which will be 1 if the session
    is already present.
    '''
    try: session_present = flags['session present']
    except KeyError: session_present = 'Info Not Available'
    LOG.debug(''.join(('Session Present flag :', str(session_present), '.')))
    if return_code != 0: # failed
        LOG.info(''.join(('Connection failed with result code <',
                          str(return_code), '>: ', _MQTT_RC[return_code], '.')))
        return
    LOG.info(''.join(('Connected! Result message: ', _MQTT_RC[return_code], '.')))
    client.mg_connected = True
    try:
        (result, mid) = client.subscribe(client.mg_topics)
    except ValueError as err:
        LOG.info(''.join(('Topic subscription error:\n\t', repr(err))))
    else:
        if result == mqtt.MQTT_ERR_NO_CONN:
            LOG.info('Attempt to subscribe without connection.')
        elif result != mqtt.MQTT_ERR_SUCCESS:
            LOG.info(''.join(('Unrecognised result <', str(result), '> during subscription.')))
        else:
            LOG.debug(''.join(('Message id <', str(mid),
                               '>: subscriptions successful to list of (topics, qos):\n\t',
                               str(client.mg_topics))))
    return

def _on_subscribe(client, userdata, mid, granted_qos):
    ''' The MQTT callback when a subscription is completed.

    Only implemented for debug purposes.
    '''
    LOG.debug(''.join(('Subscription id <', str(mid),
                       '> with (list of) qos ', str(granted_qos), '.')))
    return

def _on_disconnect(client, userdata, return_code):
    ''' The MQTT callback when a disconnection occurs.

    It sets to False the ``mg_connected`` attribute.
    '''
    LOG.info(''.join(('Client has disconnected with code <', str(return_code), '>.')))
    client.mg_connected = False

def _on_message(client, userdata, mqtt_msg):
    ''' The MQTT callback when a message is received from the MQTT broker.

    The message (topic and payload) is mapped into its internal representation and
    then appended to the incoming message list for the gateway interface to
    execute it later.
    '''
    LOG.debug(''.join(('MQTT message received:\n\t', mqttmsg_str(mqtt_msg))))
    client.on_msg_func(mqtt_msg)
    return

# pylint: enable=unused-argument

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
    def __init__(self, host='localhost', port=1883, keepalive=60, useCredentials=0, username=None, password=None, client_id='',
                 on_msg_func=None, topics=None, userdata=None):
        self._mg_host = host
        self._mg_port = port        
        if useCredentials > 0:
          self._mg_useCredentials = True
          self._mg_username = username
          self._mg_password = password  
        else:
          self._mg_useCredentials = False
        self._mg_keepalive = keepalive
        self._mg_client_id = client_id
        if on_msg_func is None: self.on_msg_func = lambda x: None
        else: self.on_msg_func = on_msg_func
        if topics is None: topics = []
        self.mg_topics = [] # list of tuples (topic, qos)
        for topic in topics:
            self.mg_topics.append((topic, 0))
        self._mg_userdata = userdata
        self.mg_connected = False

        self._mg_connect_time = 0 # time of connection request
        self.lag_test = self.lag_end # lag_test is a 'function attribute', like a method.

        super(mgClient, self).__init__(client_id=client_id, clean_session=True,
                                       userdata=userdata, protocol=mqtt.MQTTv311, transport='tcp')
        self.on_connect = _on_connect
        self.on_disconnect = _on_disconnect
        self.on_message = _on_message
        self.on_subscribe = _on_subscribe
        return

    def lag_end(self):
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
        LOG.debug(''.join(('Attempt connection to host: ', str(self._mg_host),
                           ', port: ', str(self._mg_port),
                           ', keepalive: ', str(self._mg_keepalive))))
        try:
            if self._mg_useCredentials is True:
              LOG.info("Log with credentials")
              super(mgClient, self).username_pw_set(self._mg_username, self._mg_password)
            super(mgClient, self).connect(self._mg_host, self._mg_port, self._mg_keepalive)
        except (OSError, IOError) as err:
            # the loop will try to reconnect anyway so just log an info
            LOG.info(''.join(('Client can''t connect to broker with error ', str(err))))
        # reset the 'lag' in any case, no point asking to reconnect straight away if it failed
        self.lag_reset()
        return

    def mg_reconnect(self):
        ''' Sets up the *lag* feature on top of the parent method.'''
        try:
            super(mgClient, self).reconnect()
        except (OSError, IOError) as err:
            LOG.info(''.join(('Client can''t reconnect to broker with error ', str(err))))
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
                    try: raise connectionError('Client can''t reconnect to broker.')
                    except connectionError as err: # not very elegant but works
                        if err.trigger: LOG.error(err.report)
        super(mgClient, self).loop(timeout)
