3'''
Function to initialise a logger with pre-defined handlers.

.. reviewed 30 May 2018
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

def initlogger(logger, logfiledata, emaildata):
    ''' Initialise the logging environment for the application.
from cgi import logfile

    The logger passed as parameter should be sent by the 'root' module if
    hierarchical logging is the objective. The logger is then initialised with
    the following handlers:

    - the standard 'Stream' handler will always log level WARN and above;
    - a rotating file handler, with fixed parameters (max 50kB, 3 rollover
      files); the level for this handler is DEBUG if the parameter 'log_debug' is
      True, INFO otherwise; the file name for this log is given by the
      log_filepath parameter which is used as is; an error message is logged in
      the standard handler if there was a problem creating the file;
    - an email handler with the level set to CRITICAL;

    Args:
        logger: the actual logger object to be initialised;
        logfiledata (tuple): 3 elements tuple made of
          [0] = logfilepath (string): the log file path, if None, file logging is disabled;
          [1] = filelevel (string): the level of log to be sent to the file, or NONE;
          [2] = consolelevel (string): the level of log to be sent to the console (stdout), or NONE.
        emaildata (tuple): 4 elements tuple; no email logging if either of first 3 values invalid
          [0] = host (string),
          [1] = port (int),
          [2] = address (string), ,is enabled;
          [3] = app_name (string).

    Returns:
        Nothing

    Raises:
        any IOErrors thrown by file handling methods are caught.
    '''

    logger.setLevel(logging.DEBUG) # to log ALL this function logs
    #===========================================================================
    # Reminder of various format options:
    # %(processName)s is always <MainProcess>
    # %(module)s is always the name of the current module where the log is called
    # %(filename)s is always the 'module' field with .py afterwards
    # %(pathname)s is the full path of the file 'filename'
    # %(funcName)s is the name of the function where the log has been called
    # %(name) is the name of the current logger
    #===========================================================================
    # create the stream handler. It should always work.
    formatter = logging.Formatter('%(name)-20s %(levelname)-8s: %(message)s')
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.DEBUG) # set level temporarily to log all in this function
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    # assign the logfiledata for clarity
    console_level = logfiledata[0]
    log_filepath = logfiledata[1]
    file_level = logfiledata[2]
    if not logfiledata[3]: file_num = 3
    else: file_num = logfiledata[3]
    if not logfiledata[4]: file_size = 50000
    else: file_size = logfiledata[4]
    # create the console handler, if wanted
    if console_level in _LEVELNAMES:
        formatter = logging.Formatter('%(asctime)s %(name)-20s %(levelname)-8s: %(message)s')
        cons_handler = logging.StreamHandler(sys.stdout)
        cons_handler.setLevel(_LEVELNAMES[console_level])
        cons_handler.setFormatter(formatter)
        logger.addHandler(cons_handler)
    # create the file handler, for all logs.
    if log_filepath is not None and file_level in _LEVELNAMES:
        formatter = logging.Formatter('%(asctime)s %(module)-20s %(levelname)-8s: %(message)s')
        try: file_handler = logging.handlers.RotatingFileHandler(log_filepath, maxBytes=file_size,
                                                                 backupCount=file_num)
        except (OSError, IOError) as err: # there was a problem with the file
            logger.error(''.join(('There was an error <', str(err), '> using file <', log_filepath,
                                  '> to handle logs. No file used.')))
        else:
            logger.info(''.join(('Using <', log_filepath, '> to log the <',
                                 str(file_level), '> level.')))
            file_handler.setLevel(_LEVELNAMES[file_level])
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    # create the email handler.
    email_host = emaildata [:2]
    email_address = emaildata[2]
    app_name = emaildata[3]
    if email_host[0] and email_host[1] and email_address:
        email_handler = logging.handlers. \
        SMTPHandler(email_host, email_address, email_address,
                    ''.join(('Error message from application ', app_name, '.')))
        email_handler.setLevel(logging.CRITICAL)
        email_handler.setFormatter(formatter)
        logger.addHandler(email_handler)

    stream_handler.setLevel(logging.WARN) # restore the level of the default handler
    # TODO: set the level of the logger to the minimum level needed

if __name__ == '__main__':
    pass
