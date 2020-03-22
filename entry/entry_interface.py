''' The **entry** interface class definition. Use it as a template.

.. REVIEWED 27 October 2018
'''

import logging

import serial

import mqttgateway.gateway.mqtt_map as mqtt_map

LOG = logging.getLogger(__name__)

class entryInterface(object):
    ''' The interface for the entry system.'''

    def __init__(self, params, msglist_in, msglist_out):
        # optional welcome message
        LOG.debug(''.join(('Module <', __name__, '> started.')))
        # example of how to use the 'params' dictionary
        try: port = params['port'] # the 'port' option should be defined in the configuration file
        except KeyError: # if it is not, we are toast, or a default could be provided
            errormsg = 'The "port" option is not defined in the configuration file.'
            LOG.critical(''.join(('Module ', __name__, ' could not start.\n', errormsg)))
            raise KeyError(errormsg)
        # optional success message
        LOG.debug(''.join(('Parameter "port" successfully updated with value <', port, '>')))
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
            LOG.debug(''.join(('Message <', str(msg), '> received.')))
            # given the topics subscribed to, we will only test the action
            if msg.action == 'GATE_OPEN':
                try: self._ser.write('21')
                except serial.SerialException:
                    LOG.info('Problem writing to the serial interface')
        # read the Entry System physical interface for any event
        try: data = self._ser.read(2)
        except serial.SerialException:
            LOG.info('Problem reading the serial interface')
            return
        if not data: return # no event, the read timed out
        if len(data) == 1: # not normal, log and return
            LOG.info(''.join(('Too short data read: ,', str(data), '>.')))
            return
        # now convert the 'data' into an internal message
        if data[0] == '1':
            device = 'Bell'
            if data[1] == '0': action = 'BELL_OFF'
            elif data[1] == '1': action = 'BELL_ON'
            else:
                LOG.info('Unexpected code from Entry System')
                return
        elif data[0] == '2':
            device = 'Gate'
            if data[1] == '0': action = 'GATE_CLOSE'
            elif data[1] == '1': action = 'GATE_OPEN'
            else:
                LOG.info('Unexpected code from Entry System')
                return
        msg = mqtt_map.internalMsg(iscmd=False, # it is a status message
                                   function='Security',
                                   gateway='entry2mqtt',
                                   location='gate_entry',
                                   device=device,
                                   action=action)
        self._msgl_out.push(msg)
        LOG.debug(''.join(('Message <', str(msg), '> queued to send.')))
        # let's switch on the lights now if the gate was opened
        if data == '21':
            msg = mqtt_map.internalMsg(iscmd=True,
                                       function='Lighting',
                                       location='gate_entry',
                                       action='LIGHT_ON')
            self._msgl_out.push(msg)
