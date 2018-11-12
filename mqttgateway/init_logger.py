'''Functions to create pre-defined handlers and add them to a logger.

.. REVIEWED 11 November 2018

Reminder of attributes for formatting log records
(from https://docs.python.org/2/library/logging.html#logrecord-attributes):

=================  ==================== ==============================================================
Attribute name       Format               Description
=================  ==================== ==============================================================
asctime            %(asctime)s          Human-readable time when the LogRecord was created.
                                          By default this is of the form '2003-07-08 16:49:45,896'
                                          (the numbers after the comma are millisecond portion of
                                          the time).
created            %(created)f          Time when the LogRecord was created (as returned by
                                          time.time()).
filename           %(filename)s         Filename portion of pathname. mynote: = module + '.py' for
                                          python scripts.
funcName           %(funcName)s         Name of function containing the logging call.
levelname          %(levelname)s        Text logging level for the message ('DEBUG', 'INFO',
                                          'WARNING', 'ERROR', 'CRITICAL').
levelno            %(levelno)s          Numeric logging level for the message (DEBUG, INFO,
                                           WARNING, ERROR, CRITICAL).
lineno             %(lineno)d           Source line number where the logging call was issued
                                          (if available).
module             %(module)s           Module (name portion of filename).
msecs              %(msecs)d            Millisecond portion of the time when the LogRecord was
                                          created.
message            %(message)s          The logged message, computed as msg % args.
                                          This is set when Formatter.format() is invoked.
name               %(name)s             Name of the logger used to log the call.
pathname           %(pathname)s         Full pathname of the source file where the logging call
                                          was issued (if available).
process            %(process)d          Process ID (if available).
processName        %(processName)s      Process name (if available). mynote: is always "MainProcess".
relativeCreated    %(relativeCreated)d  Time in milliseconds when the LogRecord was created,
                                          relative to the time the logging module was loaded.
thread             %(thread)d           Thread ID (if available).
threadName         %(threadName)s       Thread name (if available).
=================  ==================== ==============================================================


The argument datefmt to the Formatter class is of the form: "%Y-%m-%d %H:%M:%S".
The complete set of fields can be found here:
`time.strftime <https://docs.python.org/2/library/time.html#time.strftime>`_.

The *default* (ISO8601) formatter seems to be::

    logging.Formatter(fmt='%(asctime)s.%(msecs)03d',datefmt='%Y-%m-%d,%H:%M:%S')

The strings to use to identify the logging levels are defined in the
constant :py:data:`_LEVELNAMES`.
'''

import sys
import logging.handlers

_LEVELNAMES = {
    'CRITICAL' : logging.CRITICAL,
    'ERROR' : logging.ERROR,
    'WARN' : logging.WARNING,
    'WARNING' : logging.WARNING,
    'INFO' : logging.INFO,
    'DEBUG' : logging.DEBUG,
    'NOTSET' : logging.NOTSET
    }
''' Dictionary {"level as string": value in the logging library} '''

# Formatters
_FORMAT_NO_DATE = '%(module)s.%(lineno)d-%(funcName)s '\
                  '%(threadName)s %(levelname)s: %(message)s'
_FORMATTER_NO_DATE = logging.Formatter(fmt=_FORMAT_NO_DATE)

_FORMAT_LONG = '%(asctime)s %(module)-20s.%(lineno)04d-%(funcName)-20s '\
               '%(threadName)-10s %(levelname)-8s:\n\t%(message)s'
_FORMATTER_LONG = logging.Formatter(_FORMAT_LONG)

_FORMAT_SHORT = '%(asctime)s.%(msecs)03d %(module)-15s %(lineno)4d %(funcName)-15s '\
                '%(threadName)-10s %(levelname)-8s: %(message)s'
_FORMATTER_SHORT = logging.Formatter(_FORMAT_SHORT, datefmt="%H%M%S")

def initlogger(logger, log_data=None):
    ''' Configures a logger with pre-defined handlers based on user-defined configuration data.

    Uses :py:meth:`initloghandlers` to create the handler, check documentation there for
    more details on the format of ``log_data``.

    The logger level is forced to ``DEBUG`` here.

    Args:
        logger: the actual logger object to be initialised;
        log_data (dict): dictionary of configuration data.

    Returns:
        A string made of various lines of messages relating to what handler has been added to the
        logger.  This string can then be logged by the caller or silenced as desired.
    '''
    if log_data is None:
        logger.addHandler(logging.NullHandler) # by default
        return 'Logger returned with a NullHandler only.'
    handlers, msg = initloghandlers(log_data)
    logger.setLevel(logging.DEBUG)
    for handler in handlers:
        logger.addHandler(handler)
    return msg

def initloghandlers(log_data):
    ''' Returns a list of handlers based on user-defined configuration data.

    The ``log_data`` has to be in the form of::

            {
             'console':
                {'level': xxxx },
             'file':
                {'level': yyyy,
                 'path': zzzz,
                 'number': xxxx,
                 'size': yyyy},
             'email':
                {'host': xxxx,
                 'port': yyyy,
                 'address': zzzz,
                 'subject': xxxx }
            }

    The following handlers are created and appended to the list returned:

    - the standard 'Stream' handler, which will always log level WARN and above to stderr;
    - a console log handler;
    - a rotating file handler that requires a log level, a file path (used as is),
      the maximum size of the file and the desired number of rotating files;
    - an email handler with the level set to CRITICAL.

    The functionality is provided by the standard ``logging`` library.  Check the
    documentation for more information on the various parameters.

    Args:
        log_data (dict): dictionary of configuration data

    Returns:
        A pair made of the list of handlers and a message (string), to be logged by the caller
        or silenced as desired.
    '''
    handlers = []
    msg_list = ['Configuration of the logger:']
    # create the stream handler to stderr. It should always work.
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.WARN)
    stream_handler.setFormatter(_FORMATTER_NO_DATE) # normally the timestamp is added anyway
    handlers.append(stream_handler)
    # create the console handler
    try:
        console_data = log_data['console']
        console_level = _LEVELNAMES[console_data['level']]
    except (KeyError, IndexError) as err: # no console log
        msg_list.append(''.join(('No console log configured. Reason: ', str(err), '.')))
    else:
        cons_handler = logging.StreamHandler(sys.stdout)
        cons_handler.setLevel(console_level)
        cons_handler.setFormatter(_FORMATTER_SHORT)
        handlers.append(cons_handler)
        msg_list.append(''.join(('Console log configured to level ', console_data['level'], '.')))
    # create the file handler
    try:
        file_data = log_data['file']
        file_level = _LEVELNAMES[file_data['level']]
        file_path = file_data['path']
        if not file_path:
            raise ValueError('File path set to None or empty')
        file_num = file_data['number']
        file_size = file_data['size']
    except (KeyError, IndexError, ValueError) as err: # no file log then
        msg_list.append(''.join(('No file log configured. Reason: ', str(err), '.')))
    else:
        try: file_handler = logging.handlers.\
            RotatingFileHandler(filename=file_path,
                                mode='a',
                                maxBytes=file_size,
                                backupCount=file_num)
        except (OSError, IOError) as err: # there was a problem with the file
            msg_list.append(''.join(('No file log configured. Reason: ', str(err), '.')))
        else:
            file_handler.setLevel(file_level)
            file_handler.setFormatter(_FORMATTER_LONG)
            handlers.append(file_handler)
            msg_list.append(''.join(('File log configured to level ', file_data['level'],
                                     'using file <', file_path, '>.')))
    # create the email handler
    try:
        email_data = log_data['email']
        email_host = (email_data['host'], email_data['port'])
        if not email_host[0] or not email_host[1]:
            raise ValueError('Host and/or port set to None or empty')
        email_address = email_data['address']
        if not email_address:
            raise ValueError('Address set to None or empty')
        email_subject = email_data['subject']
    except (KeyError, ValueError) as err: # no email log
        msg_list.append(''.join(('No email log configured. Reason: ', str(err), '.')))
    else:
        email_handler = logging.handlers.\
            SMTPHandler(mailhost=email_host,
                        fromaddr=email_address,
                        toaddrs=email_address,
                        subject=email_subject)
        email_handler.setLevel(logging.CRITICAL)
        email_handler.setFormatter(_FORMATTER_LONG)
        handlers.append(email_handler)
        msg_list.append(''.join(('Email log configured to level CRITICAL using email <',
                                 str(email_address), '>.')))
    return handlers, '\n\t'.join(msg_list)

if __name__ == '__main__':
    pass
