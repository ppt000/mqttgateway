''' Application wide properties.

.. REVIEWED 11 November 2018

This module defines a singleton that hides some application-wide properties.
As any singleton, any instantiation returns always the same object.
This one specifically re-routes the ``__init__`` method to ensure that all variables
are only updated at the first instantiation and are never changed again.
The attributes are only accessible with getters and there are no setters.
'''

import sys
import logging
import logging.handlers
import os.path
import argparse
import json
from pathlib import Path
from typing import Union
import configparser

from mqttgateway import ENCODING, LIBRARY_NAME

DEFAULT_CONF_FILENAME = 'defaults.cfg'

MQTTGTW_DIR = Path(r'~/.mqttgtw').expanduser()
assert MQTTGTW_DIR.is_dir(), f"The path <*home*/.mqttgtw> does not exist or is not a directory."

LOG_DIR = MQTTGTW_DIR.joinpath('logs')

_LEVELNAMES = {
    'CRITICAL' : logging.CRITICAL,
    'ERROR' : logging.ERROR,
    'WARN' : logging.WARNING,
    'WARNING' : logging.WARNING,
    'INFO' : logging.INFO,
    'DEBUG' : logging.DEBUG,
    'NONE' : None
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

class AppProperties:
    ''' Singleton holding application properties.'''

    def __new__(cls, *args, **kwargs): # pylint: disable=protected-access, unused-argument
        if not hasattr(cls, 'singleton'):
            cls.singleton = super(AppProperties, cls).__new__(cls)
            cls.singleton._init_pointer = cls.singleton._init_singleton
        else:
            cls.singleton._init_pointer = lambda *args, **kwargs: None
        return cls.singleton

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._init_pointer(*args, **kwargs) #pylint: disable=no-member
        return

    def _init_singleton(self, app_path: Union[str, Path], app_name: str=None):
        ''' Initialisation of the properties.

        This is effectively the constructor of the class.
        At first instantiation of this singleton, the ``__init__`` method points to
        this method.
        For the following instantiations, the ``__init__`` method points to a dummy
        lambda function.

        Args:
            app_path (string): the full path of the launching script, including filename
            app_name (string): the application name if different from the filename
         '''

        # pylint: disable=attribute-defined-outside-init
        try:
            app_path = Path(app_path).resolve(strict=True)
        except FileNotFoundError as exc:
            raise RuntimeError(f"The path <{app_path}> provided"
                               f"for this application does not exist") from exc

        # Compute app_name from app_path, if not available
        self._name = app_name if app_name is not None else app_path.stem

        # Define default directories
        self._directories = [Path.home(), Path.cwd(), app_path.parent]

        # Configure the parser for the command line arguments
        parser = argparse.ArgumentParser(description=self._name)
        parser.add_argument('-c', '--cfg', help='provide the path to the configuration file',
                            dest='cfg_file', default=self._name + '.cfg')
        parser.add_argument('-m', '--map', help='provide the path to the mapping file',
                            dest='map_file', default=self._name + '.map')
        parser.add_argument('-q', '--mqtt', help='use provide the path to the mapping file',
                            dest='map_file', default=self._name + '.map')
        self._cmdline_args = parser.parse_args()

        # Find and process configuration file. The default should be in the same dir as this file
        # currently the configuration file is expected in `~/.mqttgtw`
        self._config = configparser.ConfigParser()
        with open(Path(app_path.parent, DEFAULT_CONF_FILENAME),
                  mode='rt', encoding=ENCODING) as infile:
            self._config.read_file(infile)
        del infile
        cfg_file = MQTTGTW_DIR.joinpath(self._cmdline_args.cfg_file)
        cfg_lst = self._config.read(cfg_file, encoding=ENCODING)
        if not cfg_lst:
            raise RuntimeError(f"Config file <> not found.")
        self._directories.append(cfg_lst[0])

        # Declare log attributes
        self._log_handlers = []

        warnings = [] # errors and warnings to store before logging is configured.
        log_cfg = self._config['LOG']

        # create the stream handler to stderr. It should always work.
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(logging.WARN)
        stream_handler.setFormatter(_FORMATTER_NO_DATE) # normally the timestamp is added anyway
        self._log_handlers.append(stream_handler)

        # create the console handler
        try:
            console_level = _LEVELNAMES[log_cfg['consolelevel']]
        except (KeyError, IndexError) as err:
            warnings.append(f"Config item <consolelevel> has an unrecognised"
                            f" value <{log_cfg['consolelevel']}>.")
            console_level = None
        if console_level is not None:
            cons_handler = logging.StreamHandler(sys.stdout)
            cons_handler.setLevel(console_level)
            cons_handler.setFormatter(_FORMATTER_SHORT)
            self._log_handlers.append(cons_handler)

        # create the file handler
        try:
            file_level = _LEVELNAMES[log_cfg['filelevel']]
        except (KeyError, IndexError) as err:
            warnings.append(f"Config item <filelevel> has an unrecognised"
                            f" value <{log_cfg['filelevel']}>.")
            file_level = None
        if file_level is not None:
            # create the sub-directory for the logs in case it does not exist yet
            LOG_DIR.mkdir(exist_ok=True)
            filename = LOG_DIR.joinpath(self._name + '.log')
            try:
                file_handler = logging.handlers.\
                RotatingFileHandler(filename=filename,
                                    mode='a',
                                    maxBytes=int(log_cfg['filesize']),
                                    backupCount=int(log_cfg['filenum']))
            except (OSError, IOError) as err: # there was a problem with the file
                warnings.append(''.join(('No file log configured. Reason: ', str(err), '.')))
            else:
                file_handler.setLevel(file_level)
                file_handler.setFormatter(_FORMATTER_LONG)
                self._log_handlers.append(file_handler)

        # create the journald handler
        # TODO: do it!

        lib_logger = logging.getLogger(LIBRARY_NAME)
        for handler in self._log_handlers:
            lib_logger.addHandler(handler)

        for warning in warnings:
            lib_logger.warning(warning)

        lib_logger.setLevel(logging.DEBUG)
        lib_logger.info('App initialised succesfully')

        return

    @property
    def name(self) -> str:
        ''' The name of the application.'''
        return self._name

    @property
    def cmdline_args(self) -> dict:
        ''' Command line arguments as dict.'''
        return self._cmdline_args

    @property
    def config(self) -> dict:
        ''' Configuration as dict.'''
        return self._config

    def add_handlers(self, logger: logging.Logger) -> None:
        ''' Add all the library handlers to the logger.'''
        for handler in self._log_handlers:
            logger.addHandler(handler)

    def get_path(self, path_given, extension=None, dft_name=None, dft_dirs=None):
        ''' Returns the absolute path of a file based on defined rules.

        The rules are:

        - the default name is ``dft_name`` + ``extension``;
        - the default directories are provided by the ``dft_dirs`` argument;
        - file paths can be directory only (ends with a ``/``) and are appended with the default name;
        - file paths can be absolute or relative; absolute start with a ``/`` and
          relative are prepended with the default directory;
        - file paths can be file only (no ``/`` whatsoever) and are prepended with the default directory;
        - use forward slashes ``/`` in all cases, it should work even for Windows systems;
        - however for Windows systems, use of the drive letter might be an issue and has not been tested.

        Currently this method could return a path to a file that does not exist, if a
        file corresponding to the rules is not found.

        Args:
            path_given (string): any type pf path; see rules
            extension (string): the default extension of the file
            dft_name (string): the default name to be used, usually the application name
            dft_dirs (list of strings): the default directories where to look for the file

        Returns:
            string: the full path of the file found.
        '''
        if dft_name is None: dft_name = self._name
        if dft_dirs is None: dft_dirs = self._directories
        if not extension: extension = ''
        elif extension[0] != '.': extension = '.' + extension
        if not path_given or path_given == '.': path_given = './'
        if path_given == '..': path_given = '../'
        dirname, filename = os.path.split(path_given.strip())
        if filename == '': filename = ''.join((dft_name, extension)) # default name
        dirname = os.path.normpath(dirname) # not sure it is necessary
        if os.path.isabs(dirname):
            return os.path.normpath(os.path.join(dirname, filename))
        else: # dirname is relative
            paths = [os.path.normpath(os.path.join(pth, dirname, filename)) for pth in dft_dirs]
            for pth in paths:
                if os.path.exists(pth): return pth
            return paths[0] # even if it will fail, return the first path in the list

    def get_jsonfile(self, path_given, extension=None, dft_name=None, dft_dirs=None):
        ''' Returns a dictionary with the content of the JSON file defined by the arguments.

        This method uses the :py:meth:`get_path`
        to determine the file sought.
        All the usual exceptions are raised in case of problems.
        The arguments are the same as :py:meth:`get_path`.

        Args:
            path_given (string): any type pf path; see rules
            extension (string): the default extension of the file
            dft_name (string): the default name to be used, usually the application name
            dft_dirs (list of strings): the default directories where to look for the file

        Returns:
            dict: the content of the JSON file in dictionary format.
        '''
        file_path = self.get_path(path_given, extension, dft_name, dft_dirs)
        with open(file_path, 'r') as file_handler:
            json_dict = json.load(file_handler)
        return json_dict

    """
    def init_log_handlers(self, log_data):
        ''' Creates new handlers from log_data and add the new ones to the log handlers list.

        Also updates the registered loggers with the newly created handlers.
        See method :py:meth:`initloghandlers <mqttgateway.init_logger.initloghandlers>`
        for documentation on log_data format.

        Args:
            log_data (string): see related doc for more info.

        Returns:
            string: a message indicating what has been done, to be potentially logged.
        '''
        log_handlers_list, msg = initloghandlers(log_data)
        for handler in log_handlers_list:
            if handler not in self._log_handlers:
                self._log_handlers.append(handler)
                for logger in self._loggers:
                    if handler not in logger.handlers:
                        logger.addHandler(handler)
        return msg # TODO: the message will be incorrect if there are duplicate handlers.
    """

    def register_logger(self, logger):
        ''' Register the logger and add the existing handlers to it.

        Call this method to add the logger in the registry held
        in :py:class:`AppProperties <mqttgateway.app_properties.AppProperties>`.
        Doing so, the logger will inherit all the pre-defined handlers.

        Args:
            logger (`logging.Logger` object): the logger to register
        '''
        if logger not in self._loggers:
            logger.setLevel(logging.DEBUG)
            self._loggers.append(logger)
        for handler in self._log_handlers:
            if handler not in logger.handlers:
                logger.addHandler(handler)
        return

if __name__ == '__main__':
    app = AppProperties(__file__)
    print(app.name)
    print(app.cmdline_args)
    app.config.write(sys.stdout)
