''' Application configuration.

.. REVIEWED 18 June 2022

This module defines a singleton that hides some application-wide properties.
This one specifically re-routes the ``__init__`` method to ensure that all variables
are only updated at the first instantiation and are never changed again.
The attributes are only accessible with getters and there are no setters.
'''

import sys
import logging
import logging.handlers
import argparse
import json
from pathlib import Path
import configparser
import importlib.resources as res

from mqttgateway import ENCODING, LIBRARY_NAME, VERSION

class CONFIG:
    ''' Convenience class for hard wired configuration items.'''
    DEFAULT_CFG_NAME = 'defaults.cfg'
    DEFAULT_CFG_PATH = Path(Path(__file__).parents[1], r'res/defaults.cfg')
    MQTTGTW_DIR = Path(r'~/.mqttgtw').expanduser()
    MQTTCFG_FILENAME = 'mqtt.cfg'
    LOG_DIR = MQTTGTW_DIR.joinpath('logs')

assert CONFIG.MQTTGTW_DIR.is_dir(), "The folder <*home*/.mqttgtw> does not exist"

_LEVELNAMES = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NONE': None # only used for configuration purposes
}
''' Dictionary {"level as string": value in the logging library} '''

# Log Formatters
LOGFMT ={
    'NODATE': logging.Formatter('%(module)s.%(lineno)d-%(funcName)s '
                                '%(threadName)s %(levelname)s: %(message)s'),
    'SHORT': logging.Formatter('%(asctime)s.%(msecs)03d %(module)-15s %(lineno)4d %(funcName)'
                               '-15s %(threadName)-10s %(levelname)-8s: %(message)s',datefmt="%H%M%S"),
    'LONG': logging.Formatter('%(asctime)s %(module)-20s.%(lineno)04d-%(funcName)-20s '
                              '%(threadName)-10s %(levelname)-8s:\n\t%(message)s')
}
''' Various log formatters.'''

class AppConfig:
    ''' Read-only class of application configuration.'''
    _INIT = False # True if already initialised
    _NAME = ''
    _CMDLINE_ARGS = argparse.Namespace()
    _CONFIG = configparser.ConfigParser()
    _LOG_HANDLERS = []
    _MAP_DATA = {}

    @property
    def name(self) -> str:
        ''' The name of the application.'''
        return self.__class__._NAME # pylint: disable=protected-access

    @property
    def cmdline_args(self) -> argparse.Namespace:
        ''' Command line arguments as dict.'''
        return self.__class__._CMDLINE_ARGS # pylint: disable=protected-access

    @property
    def config(self) -> configparser.ConfigParser:
        ''' Configuration as dict.'''
        return self.__class__._CONFIG # pylint: disable=protected-access

    @property
    def default_dir(self) -> Path:
        ''' The default directory.'''
        return CONFIG.MQTTGTW_DIR

    @property
    def map_data(self) -> dict:
        ''' The mapping dictionary'''
        return self.__class__._MAP_DATA # pylint: disable=protected-access

    @classmethod
    def add_handlers(cls, logger: logging.Logger) -> None:
        ''' Add all the library handlers to the logger.'''
        for handler in cls._LOG_HANDLERS: # pylint: disable=protected-access
            logger.addHandler(handler)

    @classmethod
    def init(cls, app_name: str,
             cfg: configparser.ConfigParser=None,
             map_data: dict=None) -> 'AppConfig':
        ''' Initialise the application and store its properties.'''
        if cls._INIT: return AppConfig()
        # pylint: disable=attribute-defined-outside-init

        cls._NAME = app_name

        # Configure the parser for the command line arguments
        parser = argparse.ArgumentParser(description=cls._NAME)
        parser.add_argument('-c', '--cfg', help='provide the path to the configuration file',
                            dest='cfg_file', default=cls._NAME + '.cfg')
        parser.add_argument('-m', '--map', help='provide the path to the mapping file',
                            dest='map_file', default=cls._NAME + '.json')
        cls._CMDLINE_ARGS = parser.parse_args()

        # Find and process configuration file. The default should be in the same dir as this file
        # Currently the configuration file is expected in `~/.mqttgtw`
        # ... load first the default configuration
        with res.open_text('mqttgateway.res',
                           CONFIG.DEFAULT_CFG_NAME,
                           encoding=ENCODING) as infile:
            cls._CONFIG.read_file(infile)
        del infile
        # ... load now the user configuration
        if cfg is not None: # it has been provided at runtime as an argument
            cls._CONFIG.read_dict(cfg)
        else: # find it in the default directory
            cfg_lst = [CONFIG.MQTTGTW_DIR
                       .joinpath(cls._CMDLINE_ARGS.cfg_file) # pylint: disable=no-member
                       .resolve()] # pylint: disable=no-member
            cfg_found = cls._CONFIG.read(cfg_lst, encoding=ENCODING)
            if len(cfg_found) != 1:
                raise FileNotFoundError(f"Configuration file {cfg_lst[0]} not found.")
        # ... check if the MQTT parameters should be retrieved separately
        if cls._CONFIG['MQTT']['filename']: # there is a separate MQTT config file
            cfg_lst = [CONFIG.MQTTGTW_DIR
                             .joinpath(cls._CONFIG['MQTT']['filename'])
                             .resolve()]
            cfg_found = cls._CONFIG.read(cfg_lst, encoding=ENCODING)
            if len(cfg_found) != 1:
                raise FileNotFoundError(f"Configuration file {cfg_lst[0]} not found.")

        # Configure log
        #cls._LOG_HANDLERS = [] # already done at declaration

        warnings = [] # errors and warnings to store before logging is configured.
        log_cfg = cls._CONFIG['LOG']

        # create the stream handler to stderr. It should always work.
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(logging.WARN)
        stream_handler.setFormatter(LOGFMT['NODATE']) # normally the timestamp is added anyway
        cls._LOG_HANDLERS.append(stream_handler)

        # create the console handler
        try:
            console_level = _LEVELNAMES[log_cfg['consolelevel']]
        except (KeyError, IndexError):
            warnings.append(f"Config item <consolelevel> has an unrecognised"
                            f" value <{log_cfg['consolelevel']}>.")
            console_level = None
        if console_level is not None:
            cons_handler = logging.StreamHandler(sys.stdout)
            cons_handler.setLevel(console_level)
            cons_handler.setFormatter(LOGFMT['SHORT'])
            cls._LOG_HANDLERS.append(cons_handler)

        # create the file handler
        try:
            file_level = _LEVELNAMES[log_cfg['filelevel']]
        except (KeyError, IndexError):
            warnings.append(f"Config item <filelevel> has an unrecognised"
                            f" value <{log_cfg['filelevel']}>.")
            file_level = None
        if file_level is not None:
            # create the sub-directory for the logs in case it does not exist yet
            CONFIG.LOG_DIR.mkdir(exist_ok=True)
            filename = CONFIG.LOG_DIR.joinpath(cls._NAME + '.log')
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
                file_handler.setFormatter(LOGFMT['LONG'])
                cls._LOG_HANDLERS.append(file_handler)

        # create the journald handler
        # TODO: do it!

        lib_logger = logging.getLogger(LIBRARY_NAME)
        for handler in cls._LOG_HANDLERS:
            lib_logger.addHandler(handler)

        for warning in warnings:
            lib_logger.warning(warning)

        lib_logger.setLevel(logging.DEBUG)

        # Log the configuration used ==============================================================
        lib_logger.info('=== APPLICATION STARTED ===')
        lib_logger.info(''.join(('mqttgateway version: <', VERSION, '>.')))
        lib_logger.info('Configuration options used:')
        for section in cls._CONFIG.sections():
            for option in cls._CONFIG.options(section):
                lib_logger.info("   [%s].%s : <%s>.", section, option, cls._CONFIG.get(section, option))

        # Load the map data =======================================================================
        if map_data is None and cls._CONFIG.getboolean('MAP', 'mapping'): # mapping flag
            mapfilename = cls._CONFIG.get('MAP', 'mapfilename')
            mapfilepath = CONFIG.MQTTGTW_DIR.joinpath(mapfilename).resolve(strict=True)
            try:
                with open(mapfilepath, mode='rt', encoding=ENCODING) as flh:
                    map_data = json.load(flh)
            except (OSError, IOError) as err:
                lib_logger.critical("Error loading map file: %s", err)
                raise SystemExit from err
            except ValueError as err:
                lib_logger.critical("Error reading JSON file: %s", err)
                raise SystemExit from err
        cls._MAP_DATA = map_data

        cls._INIT = True

        return AppConfig()
