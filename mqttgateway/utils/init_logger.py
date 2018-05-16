'''
Function to initialise a logger with pre-defined handlers.
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
    '''
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
        logfiledata (tuple): [0] = logfilepath (string): the log file path,
                                   if None, file logging is disabled;
                             [1] = log_debug (boolean): a flag to indicate
                                   if DEBUG logging is required, or only INFO;
                             [2] = consolelevel (string): the level of log to be sent
                                   to the console (stdout), or NONE.
        emaildata (tuple): [0] = host (string),
                           [1] = port (int),
                           [2] = address (string),
                                 if either of those 3 values are None or empty,
                                 no email logging is enabled;
                           [3] = app_name (string).

    Returns:
        Nothing

    Raises:
        any IOErrors thrown by file handling methods are caught.
    '''
    log_level = logging.INFO
    logger.setLevel(log_level) # to log this function logs
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
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO) # set the level to INFO temporarily to log what happens in this module
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    # assign the logfiledata for clarity
    log_filepath = logfiledata[0]
    log_debug = logfiledata[1]
    console_level = logfiledata[2]
    # create the console handler, if wanted
    if console_level in _LEVELNAMES:
        formatter = logging.Formatter('%(asctime)s %(name)-20s %(levelname)-8s: %(message)s')
        cons_handler = logging.StreamHandler(sys.stdout)
        cons_handler.setLevel(_LEVELNAMES[console_level])
        cons_handler.setFormatter(formatter)
        logger.addHandler(cons_handler)
    # create the file handler, for all logs.
    if log_filepath is not None:
        formatter = logging.Formatter('%(asctime)s %(module)-20s %(levelname)-8s: %(message)s')
        try: file_handler = logging.handlers.RotatingFileHandler(log_filepath, maxBytes=50000, backupCount=3)
        except (OSError, IOError) as err: # there was a problem with the file
            logger.error(''.join(('There was an error <', str(err), '> using file <', log_filepath,
                                  '> to handle logs. No file used.')))
            log_level = logging.WARN
        else:
            logger.info(''.join(('Using <', log_filepath, '> to log the ',
                                 'DEBUG' if log_debug else 'INFO', ' level.')))
            file_handler.setLevel(logging.DEBUG if log_debug else logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            log_level = logging.DEBUG if log_debug else logging.INFO
    else: log_level = logging.WARN
    # create the email handler.
    #TODO: if anything is wrong here the handler will trigger an error only when
    #      an email will be sent. Check how to check this in advance.
    email_host = emaildata [:2]
    email_address = emaildata[2]
    app_name = emaildata[3]
    if email_host is not None and email_address is not None:
        email_handler = logging.handlers. \
        SMTPHandler(email_host, email_address, email_address,
                    ''.join(('Error message from application ', app_name, '.')))
        email_handler.setLevel(logging.CRITICAL)
        email_handler.setFormatter(formatter)
        logger.addHandler(email_handler)

    logger.setLevel(log_level)
    stream_handler.setLevel(logging.WARN)

if __name__ == '__main__':
    pass
