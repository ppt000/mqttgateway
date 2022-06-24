''' The **dummy** interface class definition. Use it as a template.

.. REVIEWED 20jun22

This module defines the class :py:class:`dummyInterface` that will be instantiated by the
module :py:mod:`~mqttgateway.start_gateway`.
'''

import logging
import time

from mqttgateway import mqtt_map

LOG = logging.getLogger(__name__)

class dummyInterface:
    ''' An interface that doesn't do anything but allows to test the installation.

    The minimum requirement for the interface class is to define 2 out of 3 possible public
    methods:

    - the constructor ``__init__``,
    - either the ``loop`` method or the ``loop_start`` method,
    - a ``loop_stop`` method if a ``loop_start`` is defined.

    Args:
        params (dictionary of strings): contains all the options from the configuration file
            This dictionary is initialised by the ``[INTERFACE]`` section in
            the configuration file.  All the options in that section generate an
            entry in the dictionary. Use this to pass parameters from the configuration
            file to the interface, for example the name of a port, or the speed
            of a serial communication.
        msglist_in (:py:class:`~mqttgateway.mqtt_map.MsgList`): list of incoming messages
            in their internal representation.
        msglist_out (:py:class:`~mqttgateway.mqtt_map.MsgList`): list of outgoing messages
            in their internal representation.
    '''

    def __init__(self, params: dict, msglist_in: mqtt_map.MsgList, msglist_out: mqtt_map.MsgList):
        # optional welcome message
        LOG.debug('Module <%s> started.', __name__)
        # example of how to use the 'params' dictionary
        try: port = params['port'] # the 'port' option should be defined in the configuration file
        except KeyError as err: # if it is not, we are toast, or a default could be provided
            errormsg = 'The "port" option is not defined in the configuration file.'
            LOG.critical('Module <%s> could not start.', __name__)
            raise RuntimeError(errormsg) from err
        # optional success message
        LOG.debug('Parameter "port" successfully updated with value <%s>', port)
        # *** INITIALISE YOUR INTERFACE HERE ***

        # Keep the message lists locally
        self._msgl_in = msglist_in
        self._msgl_out = msglist_out

        # initialise time for the example; start 25s earlier so the first loop fires faster
        self.time0 = time.time() - 25

    def loop(self):
        ''' The method called periodically by the main loop.

        Place here your code to interact with your system.
        '''
        # example code to read the incoming messages list
        while True:
            msg = self._msgl_in.pull()
            if msg is None: break
            # do something with the message; here we log only
            LOG.debug('Internal message received: %s', msg)
        # example code to write in the outgoing messages list periodically
        timenow = time.time()
        if (timenow - self.time0) > 30: # every 30 seconds
            msg = mqtt_map.internalMsg(iscmd=True,
                                       function='DummyFunction',
                                       location='Office',
                                       action='MUTE_ON')
            self._msgl_out.push(msg)
            self.time0 = timenow
        return
