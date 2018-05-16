'''
An exception class that throttles events in case an error is triggered too often.

This exception can be used as a base class instead of :class:`Exception`.
It adds a counter and a timer that allow to silence the error for a while if
desired.  Only after a given period a trigger is set to indicate that a number
of errors have happened and it is time to report them.
It creates 2 members:

- ``trigger`` is a boolean set to True after the requested lag;
- ``report`` is a string giving some more information on top of the latest message.

The code using these exceptions can test the member ``trigger`` and decide to silence
the error until it is True.  At any point one can still decide to use these exceptions
as normal ones and ignore the ``trigger`` and ``report`` members.

Usage:

.. code-block:: none

    try:
        some statements that might raise your own exception derived from ThrottledException
    except YourExceptionError as err:
        if err.trigger:
            log(err.report)
'''

import time

_THROTTLELAG = 10 # in seconds

class ThrottledException(Exception):
    ''' Exception class base to throttle events

    Args:
        msg (string): the error message, as for usual exceptions, optional
        throttlelag (int): the lag time in seconds while errors should be throttled, optional
        module_name (string): the calling module to give extra information, optional

    '''
    _count = 0
    _timer = time.time()-(1.1*_THROTTLELAG)
    # the start value of _timer ensures that the first error is logged
    def __init__(self, msg=None, throttlelag=_THROTTLELAG, module_name=None):
        self.msg = msg
        self.trigger = False
        self.report = ''
        if module_name is None: modulestring = ''
        else: modulestring = ''.join((' in module ', module_name))
        now = time.time()
        lag = now - ThrottledException._timer
        if lag > throttlelag:
            self.trigger = True
            if (ThrottledException._count == 0) or (lag > (2 * throttlelag)):
                self.report = ''.join(('Fresh error', modulestring, ':\n\t -> ', msg))
            else:
                self.report = ''.join(('There have been ', str(ThrottledException._count + 1),
                                       ' errors', modulestring, ' in the past ',
                                       "{:.2f}".format(lag),
                                       ' seconds. Latest error was:\n\t -> ', msg))
            ThrottledException._count = 0
            ThrottledException._timer = now
        else:
            ThrottledException._count += 1
        super(ThrottledException, self).__init__(msg)
