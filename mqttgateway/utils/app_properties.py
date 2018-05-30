''' Application wide properties.

.. reviewed 30 May 2018

This module is an alternative to a singleton.
It keeps some application variables in the module namespace making them effectively global.
At startup, the module should be imported straight away so that it creates an AppProperties object
called Properties that is global, and initialised with mostly empty values, except the ``init``
attribute which is essentially the constructor.
'''

from collections import namedtuple
import logging
import os.path
import sys

_THIS = sys.modules[__name__]

AppProperties = namedtuple('AppProperties', ('name',
                                             'directories',
                                             'config_file_path',
                                             'root_logger',
                                             'init',
                                             'get_path',
                                             'get_logger'))

def _dummy(*args, **kwargs):
    ''' Do nothing.'''
    pass

def _get_logger(fullmodulename):
    ''' Returns the logger for the module in argument.

    Resolves the case where the module name is ``__main__``.

    Args:
        fullmodulename (string): normally it is the __name__ of the calling module.
    '''
    if fullmodulename == '__main__' or fullmodulename == _THIS.Properties.name:
        logname = _THIS.Properties.name
    else:
        modulename = fullmodulename.split('.')[-1]
        if not modulename: logname = _THIS.Properties.name
        else: logname = '.'.join((_THIS.Properties.name, modulename))
    return logging.getLogger(logname)

def _get_path(extension, path_given, app_name=None, app_dirs=None):
    ''' Returns the absolute path of a file following the application rules.

    Rules:

   - the default name is app_name + extension;
   - the default directories are provided by the app_dirs argument;
   - file paths can be directory only (ends with a '/') and are appended with the default name;
   - file paths can be absolute or relative; absolute start with a '/' and
     relative are prepended with the default directory;
   - file paths can be file only (no '/' whatsoever) and are prepended with the default directory;
   - use forward slashes '/' in any case, even for Windows systems, it should work;
   - however for Windows systems, use of the drive letter might be an issue and has not been tested.

    Args:
        extension (string): the default extension of the file
        path_given (string): any type pf path; see rules
        app_name (string): the application name for the defaults
        app_dirs (list of strings): the default directories where to look for the files
    '''
    if app_name is None: app_name = _THIS.Properties.name
    if app_dirs is None: app_dirs = _THIS.Properties.directories
    if extension[0] != '.': extension = '.' + extension # just in case
    if not path_given or path_given == '.': path_given = './'
    if path_given == '..': path_given = '../'
    dirname, filename = os.path.split(path_given.strip())
    if filename == '': filename = ''.join((app_name, extension)) # default name
    dirname = os.path.normpath(dirname) # not sure it is necessary
    if os.path.isabs(dirname):
        return os.path.normpath(os.path.join(dirname, filename))
    else: # dirname is relative
        paths = [os.path.normpath(os.path.join(pth, dirname, filename)) for pth in app_dirs]
        for pth in paths:
            if os.path.exists(pth): return pth
        return paths[0] # even if it will fail, return the first path in the list

def _init_properties(app_path=None, app_name=None):
    ''' Initialisation of the properties object.

    This is supposed to work like a constructor of the *class-like* object ``AppProperties``.
    Once called, it replaces the ``Properties`` instance with another instance initialised with
    the right values.
    The ``Properties`` object is a namedtuple to emphasize the fact that these are variables that
    should not change.  As usual, you can still mess with those but hopefully the barrier to mess
    is higher.
     '''
    if not app_name:
        app_name = os.path.splitext(os.path.basename(app_path))[0] # first part of the filename, without extension
    script_dir = os.path.realpath(os.path.dirname(app_path)) # full path of directory of launching script
    current_working_dir = os.getcwd()
    # Find configuration file
    if len(sys.argv) >= 2: pathgiven = sys.argv[1].strip()
    else: pathgiven = '' # default location in case no file name or path is given
    config_file_path = _get_path('.conf', pathgiven, app_name=app_name,
                                 app_dirs=(current_working_dir, script_dir))
    config_file_dir = os.path.dirname(config_file_path)
    dirs = (config_file_dir, current_working_dir, script_dir)
    root_logger = logging.getLogger(app_name)
    _THIS.Properties = AppProperties(app_name, dirs, config_file_path, root_logger,
                                     _dummy, _get_path, _get_logger)

Properties = AppProperties('', [], '', None, _init_properties, _dummy, _dummy)
