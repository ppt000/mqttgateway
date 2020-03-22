''' Application wide properties.

.. REVIEWED 11 November 2018

This module defines a singleton that hides some application-wide properties.
As any singleton, any instantiation returns always the same object.
This one specifically re-routes the ``__init__`` method to ensure that all variables
are only updated at the first instantiation and are never changed again.
The attributes are only accessible with getters and there are no setters.
'''

import logging
import os.path
import argparse
import json

from mqttgateway.init_logger import initloghandlers
from mqttgateway.load_config import loadconfig

DEFAULT_CONF_FILENAME = u'default.conf'

class AppProperties(object):
    ''' Singleton holding application properties.'''

    def __new__(cls, *args, **kwargs):
        # pylint: disable=protected-access
        if not hasattr(cls, 'instance'):
            #cls.instance = super(AppProperties, cls).__new__(cls, *args, **kwargs) # not for py3
            cls.instance = super(AppProperties, cls).__new__(cls)
            cls.instance._init_pointer = cls.instance._init_properties
        else:
            # changed 27Nov2018 from "cls.instance._init_pointer = cls.instance._dummy"
            cls.instance._init_pointer = lambda *args, **kwargs: None
        # pylint: enable=protected-access
        return cls.instance

    def __init__(self, *args, **kwargs):
        super(AppProperties, self).__init__() # added 27Nov2018
        self._init_pointer(*args, **kwargs)
        return

    #== Removed 27Nov2018 ==========================================================================
    # def _dummy(self, *args, **kwargs):
    #     # pylint: disable=unused-argument, no-self-use
    #     ''' Method that does nothing.'''
    #     # pylint: enable=unused-argument, no-self-use
    #     return
    #===============================================================================================

    def _init_properties(self, app_path, app_name=None, parse_dict=None):
        ''' Initialisation of the properties.

        This is effectively the constructor of the class.
        At first instantiation of this singleton, the ``__init__`` method points to
        this method.
        For the following instantiations, the ``__init__`` method points to
        the ``_dummy`` function.

        Args:
            app_path (string): the full path of the launching script, including filename
            app_name (string): the application name if different from the filename
            parse_dict (dict): not implemented
         '''

        # Define some default directories used throughout
        script_dir = os.path.realpath(os.path.dirname(app_path)) # full path of app_path
        current_working_dir = os.getcwd()
        self._directories = (current_working_dir, script_dir)
        # Compute app_name from app_path, if not available
        if not app_name:
            app_name = os.path.splitext(os.path.basename(app_path))[0] # filename without extension
        self._name = app_name
        # Configure the parser for the command line arguments
        parser = argparse.ArgumentParser(description=self._name)
        parser.add_argument('-c', '--conf', help='provide the path to the configuration file',
                            dest='config_file', default='')
        # Add the user arguments to the parser, if any
        if parse_dict:
            # TODO: to implement
            pass
        # Process the command line arguments
        self._cmdline_args = parser.parse_args()
        # Find and process configuration file. default.conf should be in the same dir as this file
        self._config = None
        config_file_path = self.get_path(self._cmdline_args.config_file.strip(),
                                         extension='.conf',
                                         dft_name=self._name,
                                         dft_dirs=self._directories)
        default_config_path = os.path.join(os.path.dirname(__file__), DEFAULT_CONF_FILENAME)
        self._config = self.load_config(default_config_path, config_file_path)
        # In this case add the configuration file directory as a default directory as well
        config_file_dir = os.path.dirname(config_file_path)
        self._directories = (config_file_dir, current_working_dir, script_dir)
        # Declare log attributes
        self._log_handlers = []
        self._loggers = []

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

    def get_file(self, path_given, extension=None, dft_name=None, dft_dirs=None):
        ''' Returns the content of the file defined by the arguments.

        This method uses the :py:meth:`get_path`
        to determine the file sought.
        All the usual exceptions are raised in case of problems.
        It is assumed the content of the file is text and that the size is small
        enough to be returned at once.
        The arguments are the same as :py:meth:`get_path`.

        Args:
            path_given (string): any type pf path; see rules
            extension (string): the default extension of the file
            dft_name (string): the default name to be used, usually the application name
            dft_dirs (list of strings): the default directories where to look for the file

        Returns:
            string: the full content of the file.
        '''
        file_path = self.get_path(path_given, extension, dft_name, dft_dirs)
        with open(file_path, 'r') as file_handler:
            file_data = file_handler.read()
        return file_data

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

    def load_config(self, cfg_dflt_string, cfg_filepath):
        # pylint: disable=no-self-use
        ''' See :py:meth:`loadconfig <mqttgateway.load_config.loadconfig>` for documentation.'''
        # pylint: enable=no-self-use
        return loadconfig(cfg_dflt_string, cfg_filepath)

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

    def get_name(self):
        ''' Name getter.

        Returns:
            string: the name of the application.
        '''
        return self._name

    def get_directories(self):
        ''' Directories getter.

        The relevant directories of the application are computed and stored at once
        at the launch of the application.  If they have been deleted, moved or their name
        is changed while the application is running, they will not be valid anymore.

        The relevant directories are the current working directory, the directory of
        the launching script and the directory where the configuration file was found
        (which could be different from the first 2 because of the option to provide it in
        the command line).

        Returns:
            list: a list of full paths of relevant directories for the application.
        '''
        return self._directories

    def get_cmdline_args(self):
        ''' Command line arguments getter.

        Returns:
            dict: the dictionary returned by ``parser.parse_args()``.

        '''
        return self._cmdline_args

    def get_config(self):
        ''' Configuration getter.

        Returns:
            dict: the dictionary returned by ``ConfigParser.RawConfigParser()``

        '''
        return self._config

if __name__ == '__main__':
    pass
