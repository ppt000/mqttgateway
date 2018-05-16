'''
The **entry** interface class definition. Use it as a template.

This module defines the class :class:`entryInterface` that will be instantiated by the
main gateway module.
Any other code needed for the interface can be placed here or in other
modules, as long as the necessary imports are included of course.
'''

import serial

import mqttgateway.gateway.mqtt_map as mqtt_map
import mqttgateway.utils.app_properties as app
_logger = app.Properties.get_logger(__name__)

class entryInterface(object):
    '''
    Doesn't do anything but provides a template.

    The minimum requirement for the interface class is to define 2 public
    methods:

    - the constructor ``__init__`` which takes 4 arguments,
    - the ``loop`` method.

    Args:
        params (dictionary of strings): contains all the options from the configuration file
            This dictionary is initialised by the ``[INTERFACE]`` section in
            the configuration file.  All the options in that section generate an
            entry in the dictionary. Use this to pass parameters from the configuration
            file to the interface, for example the name of a port, or the speed
            of a serial communication.
        msgls (pair of lists of :class:`internalMsg` objects): these lists
            represent the communication *bus* with the core of the
            application. The first list should contain the incoming messages to
            process by this interface, and the second list can be used to
            send messages from this interface to the core application (and
            subsequently to the MQTT network).  The elements of these lists
            should be instantiations of the :class:`internalMsg` class.  Use the
            method ``pop(0)`` to read the lists on a FIFO basis and
            the method ``append(msg)`` to fill the lists.
            The constructor should assign these lists to a local attribute
            that the other methods of this class can use when needed.
            It is strongly advised to *empty* the incoming list at the beginning of
            the process.  The gateway will empty all messages of the outgoing
            list and attempt to send them to the MQTT system.
            The main reason to keep 2 lists instead of one is to simplify
            sending statuses while processing incoming commands one by one.
        path (string): the full absolute path of the launcher script
            This path can be used to extract the name of the application
            or the directory where it is located.  It can be useful to
            the ``logging`` library to allow proper hierarchical logging
            or to other functions that need to find data files relative to
            the launcher script location.

    '''

    def __init__(self, params, msglist_in, msglist_out):
        # optional welcome message
        _logger.debug(''.join(('Module <', __name__, '> started.')))
        # example of how to use the 'params' dictionary
        try: port = params['port'] # the 'port' option should be defined in the configuration file
        except KeyError: # if it is not, we are toast, or a default could be provided
            errormsg = 'The "port" option is not defined in the configuration file.'
            _logger.critical(''.join(('Module ', __name__, ' could not start.\n', errormsg)))
            raise KeyError(errormsg)
        # optional success message
        _logger.debug(''.join(('Parameter "port" successfully updated with value <', port, '>')))
        # *** INITIATE YOUR INTERFACE HERE ***
        self._ser = serial.Serial(port=port, baudrate=9600, timeout=0.01)

        # Keep the message lists locally
        self._msgl_in = msglist_in
        self._msgl_out = msglist_out

    def loop(self):
        ''' The method called periodically by the main loop.

        Place here your code to interact with your system.
        '''
        # example code to read the incoming messages list
        while True:
            msg = self._msgl_in.pull()
            if msg is None: break
            # do something with the message; here we log first
            _logger.debug(''.join(('Message <', msg.str(), '> received.')))
            # given the topics subscribed to, we will only test the action
            if msg.action == 'GATE_OPEN':
                try: self._ser.write('21')
                except serial.SerialException:
                    _logger.info('Problem writing to the serial interface')
        # read the Entry System physical interface for any event
        try: data = self._ser.read(2)
        except serial.SerialException:
            _logger.info('Problem reading the serial interface')
            return
        if not data: return # no event, the read timed out
        if len(data) == 1: # not normal, log and return
            _logger.info(''.join(('Too short data read: ,', str(data), '>.')))
            return
        # now convert the 'data' into an internal message
        if data[0] == '1':
            device = 'Bell'
            if data[1] == '0': action = 'BELL_OFF'
            elif data[1] == '1': action = 'BELL_ON'
            else:
                _logger.info('Unexpected code from Entry System')
                return
        elif data[0] == '2':
            device = 'Gate'
            if data[1] == '0': action = 'GATE_CLOSE'
            elif data[1] == '1': action = 'GATE_OPEN'
            else:
                _logger.info('Unexpected code from Entry System')
                return
        msg = mqtt_map.internalMsg(iscmd=False, # it is a status message
                                   function='Security',
                                   gateway='entry2mqtt',
                                   location='gate_entry',
                                   device=device,
                                   action=action)
        self._msgl_out.push(msg)
        _logger.debug(''.join(('Message <', msg.str(), '> queued to send.')))
        # let's switch on the lights now if the gate was opened
        if data == '21':
            msg = mqtt_map.internalMsg(iscmd=True,
                                       function='Lighting',
                                       location='gate_entry',
                                       action='LIGHT_ON')
            self._msgl_out.push(msg)
