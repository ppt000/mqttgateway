'''
The **dummy** interface class definition. Use it as a template.

This module defines the class :class:`dummyInterface` that will be instantiated by the
main gateway module.
Any other code needed for the interface can be placed here or in other
modules, as long as the necessary imports are included of course.
'''

# only import this module for the example code in loop()
import time

import mqttgateway.gateway.mqtt_map as mqtt_map

import mqttgateway.utils.app_properties as app
_logger = app.Properties.get_logger(__name__)


class dummyInterface(object):
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
        # *** INITIALISE YOUR INTERFACE HERE ***

        # Keep the message lists locally
        self._msgl_in = msglist_in
        self._msgl_out = msglist_out

        # initialise time for the example only
        self.time0 = time.time()

    def loop(self):
        ''' The method called periodically by the main loop.

        Place here your code to interact with your system.
        '''
        # example code to read the incoming messages list
        while True:
            msg = self._msgl_in.pull()
            if msg is None: break
            # do something with the message; here we log only
            _logger.debug(''.join(('Message <', msg.str(), '> received.')))
        # example code to write in the outgoing messages list periodically
        timenow = time.time()
        if (timenow - self.time0) > 30: # every 30 seconds
            msg = mqtt_map.internalMsg(iscmd=True,
                                       function='DummyFunction',
                                       gateway='Dummy',
                                       location='Office',
                                       action='MUTE_ON')
            self._msgl_out.push(msg)
            self.time0 = timenow
            _logger.debug(''.join(('Message <', msg.str(), '> queued to send.')))
