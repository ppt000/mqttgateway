''' This module is the bridge between the internal and the MQTT representation of messages.

.. Reviewed 11 November 2018

As a reminder, we define the MQTT syntax as follows:

- topic::

    root/function/gateway/location/device/sender/type-{C or S}

- payload: action or status, in plain text or in a json string like ``{key1:value1,key2:value2,..}``

'''

#TODO: Review the tests in **main**
#TODO: Review position of class TokenMap as a sub-class. Take it out?

from collections import namedtuple
import Queue
import json
import paho.mqtt.client as mqtt

from mqttgateway.app_properties import AppProperties

class internalMsg(object):
    '''
    Defines all the characteristics of an internal message.

    Note about the behaviour of ``None``:
        a characteristic set to ``None`` and one set to an empty string are considered
        the same, and they both mean a non existent or missing value.
        It could be interesting to differentiate between then at a later stage as,
        for example, an empty string could still be mapped to an existing internal value,
        as if it was a default, but that is not the case here.
        Therefore ``None`` values are always converted to empty strings.

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

    def __init__(self, iscmd=False, function=None, gateway=None,
                 location=None, device=None, sender=None, action=None, arguments=None):
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

    def copy(self):
        ''' Creates a copy of the message.'''
        #TODO: use deepcopy()?
        return internalMsg(iscmd=self.iscmd,
                           function=self.function,
                           gateway=self.gateway,
                           location=self.location,
                           device=self.device,
                           sender=self.sender,
                           action=self.action,
                           arguments=self.arguments.copy())

    def str(self):
        ''' Stringifies the instance content.'''
        return ''.join(('type= ', 'C' if self.iscmd else 'S',
                        '- function= ', str(self.function),
                        '- gateway= ', str(self.gateway),
                        '- location= ', str(self.location),
                        '- device= ', str(self.device),
                        '- sender= ', str(self.sender),
                        '- action= ', str(self.action),
                        '- arguments= ', str(self.arguments)
                       ))

    def reply(self, response, reason):
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

class MsgList(Queue.Queue, object):
    ''' Message list to communicate between the library and the interface.

    Defined as a Queue list in case the library is used in multi-threading mode.

    The methods are called ``push`` and ``pull`` in order to differentiate them from the
    *usual* names (put, get, append, pop, ...).
    '''
    #TODO: implement maxsize and timeout.

    def __init__(self):
        super(MsgList, self).__init__(maxsize=0)

    def push(self, item, block=True, timeout=None):
        ''' Pushes the item at the end of the list.

        Equivalent to append or put in other list implementations.
        The ``block`` and ``timeout`` arguments have the same meaning
        as in the ``Queue`` library.

        Args:
            item (object): the object to push in the list
            block (boolean): in case the list is full
            timeout (float): wait time if block == True
        '''
        super(MsgList, self).put(item, block, timeout)

    def pull(self, block=False, timeout=None):
        ''' Pull the first item from the list.

        Equivalent to pop or get in other list implementations.
        The ``block`` and ``timeout`` arguments have the same meaning
        as in the ``Queue`` library.

        Args:
            block (boolean): in case the list is empty
            timeout (float): wait time if block == True
        '''
        try: item = super(MsgList, self).get(block, timeout)
        except Queue.Empty: return None
        super(MsgList, self).task_done()
        return item

mappedTokens = namedtuple('mappedTokens', ('function', 'gateway', 'location', 'device', 'sender',
                                           'action', 'argkey', 'argvalue'))
''' Tokens representing a message that can be mapped.'''

NO_MAP = {
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

class msgMap(object):
    ''' Contains the mapping data and the conversion methods.

    The mapping data is read from a JSON style dictionary.
    To access the maps use::

        mqtt_token = maps.*field*.i2m(internal_token)

    Example::

        mqtt_token = maps.gateway.i2m(internal_token)

    Args:
        jsondict (dictionary): contains the map data in the agreed format;
                               if None, the NO_MAP structure is used.

    '''

    class tokenMap(object):
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
        def __init__(self, maptype, mapdict=None):
            if not mapdict or maptype == 'none':
                self.i2m_dict = None
                self.m2i_dict = None
                self.mapfunc = self._mapnone # by default with no maps
                self.maptype = 'none'
            else:
                self.i2m_dict = {k: v[0] for k, v in mapdict.iteritems()}
                self.m2i_dict = {w: k for k, v in mapdict.iteritems() for w in v}
                if maptype == 'loose':
                    self.mapfunc = self._maploose
                    self.maptype = maptype
                elif maptype == 'strict':
                    self.mapfunc = self._mapstrict
                    self.maptype = maptype
                else:
                    self.mapfunc = self._mapnone # by default if unknown maptype
                    self.maptype = 'none'

        def m2i(self, mqtt_token):
            ''' Generic method converting an MQTT token into an internal characteristic.'''
            return self.mapfunc(mqtt_token, self.m2i_dict)

        def i2m(self, internal_token):
            ''' Generic method converting an internal characteristic into an MQTT token.'''
            mqtt_token = self.mapfunc(internal_token, self.i2m_dict)
            return mqtt_token

        @staticmethod
        def _mapnone(token, dico):
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
        def _maploose(token, dico):
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
        def _mapstrict(token, dico):
            ''' Returns the argument converted if in dictionary, raises exception otherwise.

            If ``token`` is None, it is always converted in an empty string.
            An empty string is kept as an empty string, even if not in the dictionary.

            Args:
                token (string): the token to convert
                dico (dictionary): the mapping dictionary to use for the conversion, if needed

            Returns:
                string: converted token
            '''
            if token is None or token == '': return ''
            try: return dico[token]
            except KeyError: raise ValueError(''.join(('Token <', token, '> not found.')))

    def __init__(self, jsondict=None):
        if not jsondict: jsondict = NO_MAP
        self._sender = AppProperties().get_name()
        try: self.root = jsondict['root']
        except KeyError: raise ValueError('JSON dictionary has no key <root>.')
        try: self.topics = jsondict['topics']
        except KeyError: raise ValueError('JSON dictionary has no key <topics>.')

        maplist = []
        for field in mappedTokens._fields:
            try: field_data = jsondict[field]
            except KeyError:
                raise ValueError(''.join(('JSON dictionary has no key <', field, '>.')))
            try: field_maptype = field_data['maptype']
            except KeyError:
                raise ValueError(''.join(('<', field, '> object has no child <maptype>.')))
            if field_maptype == 'none':
                field_map = None
            else:
                try: field_map = field_data['map']
                except KeyError:
                    raise ValueError(''.join(('<', field, '> object has no child <map>.')))
            maplist.append(self.tokenMap(field_maptype, field_map))
        self.maps = mappedTokens._make(maplist)

    def sender(self):
        ''' Getter for the ``_sender`` attribute.'''
        return self._sender

    def mqtt2internal(self, mqtt_msg):
        '''
        Converts the MQTT message into an internal one.

        Args:
            mqtt_msg (mqtt.MQTTMessage): a MQTT message.

        Returns:
            internalMsg object: the conversion of the MQTT message

        Raises:
            ValueError: in case of bad MQTT syntax or unrecognised map elements
        '''

        # unpack the topic
        tokens = mqtt_msg.topic.split('/')
        if len(tokens) != 7:
            raise ValueError(''.join(('Topic <', mqtt_msg.topic,
                                      '> has not the right number of tokens.')))

        # unpack the arguments if any
        # one of them should be 'action' and goes into mqtt_action
        # the other arguments form a dictionary: m_args
        if mqtt_msg.payload[0] == '{': # it is a JSON structure
            try: m_args = json.loads(mqtt_msg.payload)
            except (ValueError, TypeError) as err:
                raise ValueError(''.join(('Bad format for payload <', mqtt_msg.payload, '>'\
                                          ' with error:\n\t', str(err))))
            try: mqtt_action = m_args.pop('action')
            except KeyError:
                raise ValueError(''.join(('No action found in payload <', mqtt_msg.payload, '>')))
        else: # this is a straightforward action
            mqtt_action = mqtt_msg.payload
            m_args = {}

        function = self.maps.function.m2i(tokens[1])
        gateway = self.maps.gateway.m2i(tokens[2])
        location = self.maps.location.m2i(tokens[3])
        device = self.maps.device.m2i(tokens[4])
        sender = self.maps.sender.m2i(tokens[5])
        action = self.maps.action.m2i(mqtt_action)
        i_args = {}
        for key, value in m_args.iteritems():
            i_args[self.maps.argkey.m2i(key)] = self.maps.argvalue.m2i(value)

        if tokens[6] == 'S': iscmd = False
        elif tokens[6] == 'C': iscmd = True
        else:
            raise ValueError(''.join(('Type in topic <', mqtt_msg.topic, '> not recognised.')))

        return internalMsg(iscmd=iscmd,
                           function=function,
                           gateway=gateway,
                           location=location,
                           device=device,
                           sender=sender,
                           action=action,
                           arguments=i_args)

    def internal2mqtt(self, internal_msg):
        '''
        Converts an internal message into a MQTT one.

        Args:
            internal_msg (:class:`internalMsg`): the message to convert

        Returns:
            a MQTTMessage object: a full MQTT message where topic syntax is
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
        for key, value in internal_msg.arguments.iteritems():
            mqtt_args[self.maps.argkey.i2m(key)] = self.maps.argvalue.i2m(value)
        # Generate topic
        topic = '/'.join((self.root, mqtt_function, mqtt_gateway, mqtt_location,
                          mqtt_device, mqtt_sender, 'C' if internal_msg.iscmd else 'S'))
        # Generate payload
        if not mqtt_args: # no arguments, just publish the action text on its own
            payload = mqtt_action
        else: # there are arguments, publish them
            mqtt_args['action'] = mqtt_action
            try: payload = json.dumps(mqtt_args)
            except (ValueError, TypeError) as err:
                raise ValueError(''.join(('Error serialising arguments:\n\t', str(err))))

        mqtt_msg = mqtt.MQTTMessage()
        mqtt_msg.topic = topic
        mqtt_msg.payload = payload
        mqtt_msg.qos = 0
        mqtt_msg.retain = False
        return mqtt_msg

def test():
    ''' Test function. '''
    # load a valid map in JSON format
    jsonfilepath = './test_map2.json'
    with open(jsonfilepath, 'r') as json_file:
        json_data = json.load(json_file)
    # instantiate a class
    msgmap = msgMap(json_data)
    # printout some members
    function = msgmap.maps.function.m2i('lighting'); print function
    gateway = msgmap.maps.gateway.m2i('dummy'); print gateway
    location = msgmap.maps.location.m2i('office'); print location
    device = msgmap.maps.device.m2i('kitchen_track'); print device
    sender = msgmap.maps.sender.m2i('me'); print sender
    action = msgmap.maps.action.m2i('light_on'); print action
    m_args = {'key1': 'value1'}
    i_args = {}
    for key, value in m_args.iteritems():
        i_args[msgmap.maps.argkey.m2i(key)] = msgmap.maps.argvalue.m2i(value)
    print i_args

def reverse():
    ''' Another test function.'''
    jsonfilepath = './test_map.json'
    with open(jsonfilepath, 'r') as json_file:
        json_data = json.load(json_file)
    for item in ('function', 'gateway', 'location', 'device', 'sender', 'action', 'argkey', 'argvalue'):
        if 'map' not in json_data[item]: continue
        newmap = {}
        oldmap = json_data[item]['map']
        for key, value in oldmap.iteritems():
            newmap[value] = []
            newmap[value].append(key)
        json_data[item]['map'] = newmap
    print json.dumps(json_data)
    return

if __name__ == '__main__':
    test()
    #reverse()
