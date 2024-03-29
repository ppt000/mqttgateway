''' This module is the bridge between the internal and the MQTT representation of messages.

.. Reviewed 20jun22

As a reminder, we define the MQTT syntax as follows:

- topic::

    root/function/gateway/location/device/sender/type-{C or S}

- payload: action or status, in plain text or in a json string like ``{key1:value1,key2:value2,..}``

'''

#TODO: Review position of class TokenMap as a sub-class. Take it out?

import logging
from collections import namedtuple
import json
import queue
from copy import deepcopy

import paho.mqtt.client as mqtt

from mqttgateway.app_config import AppConfig
from mqttgateway import ENCODING

LOG = logging.getLogger(__name__)

class internalMsg:
    '''
    Defines all the characteristics of an internal message.

    Note about the behaviour of ``None``:
        a characteristic set to ``None`` and one set to an empty string are considered
        the same, and they both mean a non existent or missing value.
        It could be interesting to differentiate between then at a later stage as,
        for example, an empty string could still be mapped to an existing internal value,
        as if it was a default, but that is not the case here.
        Therefore ``None`` values are always converted to empty strings.

    TODO: implement smart retrieval of arguments with key checks

    Args:
        iscmd (bool): Indicates if the message is a command (True) or a status (False)
        function (string): internal representation of function
        gateway (string): internal representation of gateway
        location (string): internal representation of location
        device (string): internal representation of device
        sender (string): internal representation of sender
        action (string): internal representation of action
        arguments (dictionary of strings): all values should be assumed to be strings

    '''

    def __init__(self, iscmd: bool=False, function: str=None, gateway: str=None,
                 location: str=None, device: str=None, sender: str=None,
                 action: str=None, arguments: dict=None):
        self.iscmd = iscmd
        if function is None: self.function = ''
        else: self.function = function
        if gateway is None: self.gateway = ''
        else: self.gateway = gateway
        if location is None: self.location = ''
        else: self.location = location
        if device is None: self.device = ''
        else: self.device = device
        if sender is None: self.sender = ''
        else: self.sender = sender
        if action is None: self.action = ''
        else: self.action = action
        if arguments is None: self.arguments = {}
        else: self.arguments = arguments
        return

    def clear(self):
        ''' Clears all content of the message.'''
        self.iscmd = False
        self.function = ''
        self.gateway = ''
        self.location = ''
        self.device = ''
        self.sender = ''
        self.action = ''
        self.arguments = {}
        return

    def copy(self) -> 'internalMsg':
        ''' Creates a copy of the message.'''
        return internalMsg(iscmd=self.iscmd,
                           function=self.function,
                           gateway=self.gateway,
                           location=self.location,
                           device=self.device,
                           sender=self.sender,
                           action=self.action,
                           arguments=self.arguments.copy())

    def argument(self, arg: any, raises: bool=False, default: any=None) -> any:
        ''' Return the argument if found in the arguments dictionary.'''
        try: return self.arguments[arg]
        except KeyError as err:
            if raises:
                raise ValueError(f"Argument {arg} not found in arguments dictionary") from err
            LOG.warning('Argument %s not found in arguments dictionary', arg)
            return default

    def __str__(self) -> str:
        ''' Stringifies the instance content.'''
        return ' - '.join(('type=' + 'C' if self.iscmd else 'S',
                        'function=' + str(self.function),
                        'gateway=' + str(self.gateway),
                        'location=' + str(self.location),
                        'device=' + str(self.device),
                        'sender=' + str(self.sender),
                        'action=' + str(self.action),
                        'arguments=' + str(self.arguments)
                       ))

    def reply(self, response: str, reason: str) -> 'internalMsg':
        ''' Formats the message to be sent as a reply to an existing command

        This method is supposed to be used with an existing message that has been received.
        Using this method for all replies guarantees a consistent syntax for replies.

        Args:
            response (string): code or abbreviation for response, e.g. ``OK```or ``ERROR``
            reason (string): longer description of the responses
        '''
        #TODO: elaborate
        self.iscmd = False
        self.arguments['response'] = response
        self.arguments['reason'] = reason
        return self

class MsgList(queue.Queue):
    ''' Message list to communicate between the library and the interface.

    Defined as a Queue list in case the library is used in multi-threading mode.

    The methods are called ``push`` and ``pull`` in order to differentiate them from the
    *usual* names (put, get, append, pop, ...).
    '''
    #TODO: implement maxsize and timeout.

    def __init__(self):
        super().__init__(maxsize=0)

    def push(self, item: any, block: bool=True, timeout: int=None):
        ''' Pushes the item at the end of the list.

        Equivalent to append or put in other list implementations.
        The ``block`` and ``timeout`` arguments have the same meaning
        as in the ``Queue`` library.

        Args:
            item (object): the object to push in the list
            block (boolean): in case the list is full
            timeout (float): wait time if block == True
        '''
        #LOG.debug('Queue size before push is %d', super().qsize())
        super().put(item, block, timeout)
        #LOG.debug('Queue size after push is %d', super().qsize())

    def pull(self, block: bool=False, timeout: int=None) -> any:
        ''' Pull the first item from the list.

        Equivalent to pop or get in other list implementations.
        The ``block`` and ``timeout`` arguments have the same meaning
        as in the ``Queue`` library.

        Args:
            block (boolean): in case the list is empty
            timeout (float): wait time if block == True
        '''
        try: item = super().get(block, timeout)
        except queue.Empty: return None
        #LOG.debug('Queue size after pull is %d', super().qsize())
        super().task_done()
        return item

mappedTokens = namedtuple('mappedTokens', ('function', 'gateway', 'location', 'device', 'sender',
                                           'action', 'argkey', 'argvalue'))
''' Tokens representing a message that can be mapped.'''

BASE_MAP = {
    'root': '',
    'topics': [],
    'function': {'maptype': 'none'},
    'gateway': {'maptype': 'none'},
    'location': {'maptype': 'none'},
    'device': {'maptype': 'none'},
    'sender': {'maptype': 'none'},
    'action': {'maptype': 'none'},
    'argkey': {'maptype': 'none'},
    'argvalue': {'maptype': 'none'}
}
'''Default map, with no mapping at all.'''

class msgMap:
    ''' Contains the mapping data and the conversion methods.

    The mapping data is read from a JSON style dictionary.
    To access the maps use::

        mqtt_token = maps.*field*.i2m(internal_token)

    Example::

        mqtt_token = maps.gateway.i2m(internal_token)

    Args:
        jsondict (dictionary): contains the map data in the agreed format,
                               or part of it, it will be complemented.
    '''

    class tokenMap:
        ''' Represents the mapping for a given token or characteristic.

        Each instantiation of this class represent the mapping for a given
        token, and contains the type of mapping, the mapping dictionary if
        available, and the methods to convert the keywords back and forth between
        MQTT and internal representation.

        The mapping dictionary passed as argument has the internal keywords as keys and
        as value a list of corresponding MQTT keywords.  Only the first of the list will be
        used for the reverse dictionary, the other MQTT keywords being 'aliases'.

        Args:
            maptype (string): type of map, should be either 'strict'. 'loose' or 'none'
            mapdict (dictionary): dictionary representing the mapping
        '''
        def __init__(self, maptype: str, mapdict: dict=None):
            if not mapdict or maptype == 'none':
                self.i2m_dict = None
                self.m2i_dict = None
                self.mapfunc = self._mapnone # by default with no maps
                self.maptype = 'none'
            else:
                self.i2m_dict = {k: v[0] for (k, v) in mapdict.items()}
                self.m2i_dict = {w: k for (k, v) in mapdict.items() for w in v}
                if maptype == 'loose':
                    self.mapfunc = self._maploose
                    self.maptype = maptype
                elif maptype == 'strict':
                    self.mapfunc = self._mapstrict
                    self.maptype = maptype
                else:
                    self.mapfunc = self._mapnone # by default if unknown maptype
                    self.maptype = 'none'

        def m2i(self, mqtt_token: str) -> str:
            ''' Generic method converting an MQTT token into an internal characteristic.'''
            return self.mapfunc(mqtt_token, self.m2i_dict)

        def i2m(self, internal_token: str) -> str:
            ''' Generic method converting an internal characteristic into an MQTT token.'''
            mqtt_token = self.mapfunc(internal_token, self.i2m_dict)
            return mqtt_token

        @staticmethod
        def _mapnone(token: str, dico: dict) -> str:
            # pylint: disable=unused-argument
            ''' Returns the argument unchanged.

            Args:
                token (string): the token to convert
                dico (dictionary): the mapping dictionary to use for the conversion, if needed

            Returns:
                string: converted token
            '''
            if token is None: return ''
            return token
            # pylint: enable=unused-argument

        @staticmethod
        def _maploose(token: str, dico: dict) -> str:
            ''' Returns the argument converted if in dictionary, unchanged otherwise.

            If ``token`` is None, it is always converted in an empty string.

            Args:
                token (string): the token to convert
                dico (dictionary): the mapping dictionary to use for the conversion, if needed

            Returns:
                string: converted token
            '''
            if token is None: return ''
            try: return dico[token]
            except KeyError: return token

        @staticmethod
        def _mapstrict(token: str, dico: dict) -> str:
            ''' Returns the argument converted if in dictionary, raises exception otherwise.

            If ``token`` is None, it is always converted in an empty string.
            An empty string is kept as an empty string, even if not in the dictionary.

            Args:
                token (string): the token to convert
                dico (dictionary): the mapping dictionary to use for the conversion, if needed

            Returns:
                string: converted token
            '''
            if token is None: token = ''
            try:
                return dico[token]
            except KeyError as err:
                raise ValueError(f"Token <{token}> not found.") from err

    def __init__(self, jsondict: dict=None):
        map_dct = deepcopy(BASE_MAP)
        map_dct.update(jsondict)
        self._sender = AppConfig().name
        self.root = map_dct['root']
        self.topics = map_dct['topics']

        maplist = []
        for field in mappedTokens._fields:
            field_data = map_dct[field]
            try:
                field_maptype = field_data['maptype']
            except KeyError as err:
                raise ValueError(f"<{field}> object has no child <maptype>.") from err
            if field_maptype == 'none':
                field_map = None
            else:
                try:
                    field_map = field_data['map']
                except KeyError as err:
                    raise ValueError(f"<{field}> object has no child <map>.") from err
            maplist.append(self.tokenMap(field_maptype, field_map))
        self.maps = mappedTokens._make(maplist)

    def sender(self):
        ''' Getter for the ``_sender`` attribute.'''
        # TODO: convert to property
        return self._sender

    def mqtt2internal(self, mqtt_msg: mqtt.MQTTMessage) -> internalMsg:
        '''
        Converts the MQTT message into an internal one.

        Args:
            mqtt_msg (:class:`mqtt.MQTTMessage`): a MQTT message.

        Returns:
            :class:`internalMsg`: the conversion of the MQTT message

        Raises:
            ValueError: in case of bad MQTT syntax or unrecognised map elements
        '''

        # unpack the topic
        tokens = mqtt_msg.topic.split('/')
        if len(tokens) != 7:
            raise ValueError(f"Topic <{mqtt_msg.topic}> has not the right number of tokens.")
        # encode payload in a string, it is a <bytes> in the message
        payload = mqtt_msg.payload.decode(ENCODING)
        # unpack the arguments if any
        # one of them should be 'action' and goes into mqtt_action
        # the other arguments form a dictionary: m_args
        if payload[0] == '{': # it is a JSON structure
            try: m_args = json.loads(payload)
            except (ValueError, TypeError) as err: # TODO: use JSON decode error
                raise ValueError(f"Bad format for payload <{payload}>") from err
            try: mqtt_action = m_args.pop('action')
            except KeyError as err:
                raise ValueError(f"No action found in payload <{payload}>") from err
        else: # this is a straightforward action
            mqtt_action = payload
            m_args = {}

        function = self.maps.function.m2i(tokens[1])
        gateway = self.maps.gateway.m2i(tokens[2])
        location = self.maps.location.m2i(tokens[3])
        device = self.maps.device.m2i(tokens[4])
        sender = self.maps.sender.m2i(tokens[5])
        action = self.maps.action.m2i(mqtt_action)
        i_args = {}
        for (key, value) in m_args.items():
            i_args[self.maps.argkey.m2i(key)] = self.maps.argvalue.m2i(value)

        if tokens[6] == 'S': iscmd = False
        elif tokens[6] == 'C': iscmd = True
        else:
            raise ValueError(f"Type in topic <{mqtt_msg.topic}> not recognised.")

        return internalMsg(iscmd=iscmd,
                           function=function,
                           gateway=gateway,
                           location=location,
                           device=device,
                           sender=sender,
                           action=action,
                           arguments=i_args)

    def internal2mqtt(self, internal_msg: internalMsg) -> mqtt.MQTTMessage:
        '''
        Converts an internal message into a MQTT one.

        Args:
            internal_msg (:class:`internalMsg`): the message to convert

        Returns:
            a MQTTMessage: a full MQTT message where topic syntax is
            ``root/function/gateway/location/device/sender/{C or S}`` and
            payload syntax is either a plain action or a JSON string.

        Raises:
            ValueError: in case a token conversion fails
        '''

        mqtt_function = self.maps.function.i2m(internal_msg.function)
        mqtt_gateway = self.maps.gateway.i2m(internal_msg.gateway)
        mqtt_location = self.maps.location.i2m(internal_msg.location)
        mqtt_device = self.maps.device.i2m(internal_msg.device)
        mqtt_sender = self.maps.sender.i2m(internal_msg.sender)
        if not mqtt_sender: mqtt_sender = self._sender
        mqtt_action = self.maps.action.i2m(internal_msg.action)
        mqtt_args = {}
        for (key, value) in internal_msg.arguments.items():
            mqtt_args[self.maps.argkey.i2m(key)] = self.maps.argvalue.i2m(value)
        # Generate topic
        topic = '/'.join((self.root, mqtt_function, mqtt_gateway, mqtt_location,
                          mqtt_device, mqtt_sender, 'C' if internal_msg.iscmd else 'S'))
        # Generate payload
        if not mqtt_args: # no arguments, just publish the action text on its own
            payload = mqtt_action
        else: # there are arguments, publish them
            if mqtt_action: mqtt_args['action'] = mqtt_action # add action only if not empty
            try: payload = json.dumps(mqtt_args)
            except (ValueError, TypeError) as err:
                raise ValueError('Error serialising arguments') from err

        mqtt_msg = mqtt.MQTTMessage()
        mqtt_msg.topic = topic.encode('utf-8')
        mqtt_msg.payload = payload.encode('utf-8')
        mqtt_msg.qos = 0
        mqtt_msg.retain = False
        return mqtt_msg
