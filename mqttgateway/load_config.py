''' Function to facilitate the loading of configuration parameters.

.. REVIEWED 11 November 2018

Based on the standard library ConfigParser.
'''

import os.path

# PY2
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
    
def loadconfig(cfg_dflt_path, cfg_filepath):
    ''' Load the configuration from a file based on a default one.

    This function uses the standard library ``ConfigParser``.

    The objective of this function is to provide a mechanism to ensure that all
    the options that are expected by the application are defined and will not need
    to be checked throughout the code.  To achieve that, a default configuration needs
    to be provided, represented by the string ``cfg_dflt_path`` passed as argument.
    This string is expected to have all the necessary
    sections and options that the application will need, with their default
    values.
    All options need to be listed there, even the ones that HAVE to be
    updated and have no default value.

    The function loads this default configuration, then checks if the
    configuration file is available, and if found it grabs only the values from
    the file that are also present in the default configuration.  Anything else
    in the file is not considered, except for the ``[INTERFACE]`` section (see below).
    The result is a configuration object with all
    the necessary fields, updated by the values in the configuration file,
    if present, or with the default values if not.
    The application can therefore call all fields without checking for their existence.

    The exception to the above process in the ``[INTERFACE]`` section, which is the section
    reserved for the developper of the gateway to define its own specific options.
    The options of this section will be loaded 'as is' in the Config object.
    These options will be sent to the interface through a dedicated dictionary.
    It is then up to the developper of the interface to check their velidity or provide
    its own defaults for these options.

    Finally, the function updates the option ``location`` in the
    section ``[CONFIG]`` with the full path of the configuration file used, so that it can be
    checked or logged if desired later.  This allows to make sure which file has been loaded
    in case there is some ambiguity.
    The function also 'logs' the error in the 'error' option of the
    same section, if any OS exception occurred while opening or reading the configuration file.

    Args:
        cfg_dflt_path (string): represents the default configuration.
        cfg_filepath (string): the path of the configuration file; it is used 'as is'
            and if it is relative there is no guarantee of where it will actually point.
            It is preferrable to send a valid absolute path.

    Returns:
        dict: ``configparser.ConfigParser`` object loaded with the options of the configuration.
    '''
    # Load the default configuration
    cfg_dflt = configparser.ConfigParser(allow_no_value=True)
    cfg_dflt.add_section('CONFIG')
    try:
        with open(cfg_dflt_path, 'r') as file_handle:
            cfg_dflt.readfp(file_handle)
    except (OSError, IOError) as err:
        raise # TODO: do something else?
    cfg_file = configparser.ConfigParser()
    try:
        with open(cfg_filepath, 'r') as file_handle:
            cfg_file.readfp(file_handle)
    except (OSError, IOError) as err:
        # 'log' the error in the ConfigParser object
        cfg_dflt.set('CONFIG', 'error', ''.join(('Error <', str(err),
                                                 '> with file <', cfg_filepath, '>.')))
        # return the default configuration as there was a problem reading the file
        return cfg_dflt
    # 'merge' it with the default configuration
    for section in cfg_dflt.sections():
        if cfg_file.has_section(section):
            for option in cfg_dflt.options(section):
                if cfg_file.has_option(section, option):
                    cfg_dflt.set(section, option, cfg_file.get(section, option))
    # Deal with the [INTERFACE] section now
    if cfg_file.has_section('INTERFACE'):
        if not cfg_dflt.has_section('INTERFACE'):
            cfg_dflt.add_section('INTERFACE')
        for option in cfg_file.options('INTERFACE'):
            cfg_dflt.set('INTERFACE', option, cfg_file.get('INTERFACE', option))
    # Create or overwrite the 'location' option in section [CONFIG] if the section exists.
    location = os.path.realpath(file_handle.name)
    cfg_dflt.set('CONFIG', 'location', location)
    return cfg_dflt
