'''
docstring
'''

from collections import namedtuple
import logging
import os.path
import sys

_THIS = sys.modules[__name__]

AppProperties = namedtuple('AppProperties', ('name', 'path', 'root_logger', 'init', 'get_path', 'get_logger'))

def __dummy(*args, **kwargs):
    pass

def __get_logger(fullmodulename):
    ''' docstring '''
    if fullmodulename == '__main__' or fullmodulename == _THIS.Properties.name:
        logname = _THIS.Properties.name
    else:
        modulename = fullmodulename.split('.')[-1]
        if not modulename: logname = _THIS.Properties.name
        else: logname = '.'.join((_THIS.Properties.name, modulename))
    return logging.getLogger(logname)

def __get_path(extension, path_given=None):
    '''
    Generates the full absolute path of a file.

    This function builds an absolute path to a file based on 3 'default' arguments
    (the basename of the file, the extension of the file, and an absolute path) and
    an extra argument that represents a valid path.
    Depending on what represents this path (a directory, a file, an absolute or a
    relative reference) the function will generate a full absolute path, relying on the
    'default' parameters if and when necessary.
    The generation of the full path follows those rules:

        - the default name is made of the default basename and the default extension;
        - if the path given is empty, then the full path is the default absolute path
          with the default filename;
        - if the path given contains a filename at the end, this is the filename to be used;
        - if the path given contains an absolute path at the beginning, that is the
          absolute path that will be used;
        - if the path given contains only a relative path at the beginning, then
          the default absolute path will be prepended to the path given.

    Args:
        basename (string): basename without extension, usually the application name
        absdirpath (string): the absolute path of the current application
        ext (string): the extension of the file, in the form '.xxx'. i.e. with the dot
        pathgiven (string): the path given as alternative to the default
    Returns:
        string: a full absolute path
    '''
    dfltname = ''.join((_THIS.Properties.name, extension))
    if path_given == '':
        filepath = os.path.join(_THIS.Properties.path, dfltname)
    else:
        dirname, filename = os.path.split(path_given.strip())
        if dirname != '': dirname = os.path.normpath(dirname)
        if filename == '': filename = dfltname
        if dirname == '': dirname = _THIS.Properties.path
        elif not os.path.isabs(dirname): dirname = os.path.join(_THIS.Properties.path, dirname)
        filepath = os.path.join(dirname, filename)
    return os.path.normpath(filepath)

def __init_properties(full_path):
    name = os.path.splitext(os.path.basename(full_path))[0] # first part of the filename, without extension
    path = os.path.realpath(os.path.dirname(full_path)) # full path of the launching script
    root_logger = logging.getLogger(name)
    _THIS.Properties = AppProperties(name, path, root_logger, __dummy, __get_path, __get_logger)

Properties = AppProperties('', '', None, __init_properties, __dummy, __dummy)
