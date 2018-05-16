'''
Function to facilitate the loading of configuration parameters.
Based on ConfigParser.
'''

import ConfigParser
import io
import os.path

def loadconfig(cfg_dflt_string, cfg_filepath):
    '''
    The configuration is loaded with the help of the python library ConfigParser
    and the following convention.

    The default configuration is represented by the string passed as argument
    ``cfg_dflt_string``. This string is expected to have all the necessary
    sections and options that the application will need, with their default
    values.  All options need to be listed there, even the ones that HAVE to be
    updated and have no default value.  This default configuration will be
    usually declared in the caller module as a constant string, and will be used
    as a template for the actual configuration file.

    The function 'loads' this default configuration, then checks if the
    configuration file is available, and if found it grabs only the values from
    the file that are also present in the default configuration.  Anything else
    in the file is not considered, except for the [INTERFACE] section (see below).
    The result is a configuration object with all
    the necessary fields, updated by the file values if present, or with the
    default values if not. The application can therefore call all fields without
    index errors.

    The exception to the above process in the [INTERFACE] section.  The options
    of this section will be loaded 'as is' in the Config object.  This section can be
    used to define ad-hoc options that are not in the default configuration.

    Finally, the function updates the option 'location' in the
    section [CONFIG] with the full path of the configuration file used, just in
    case it is needed later.  However it only updates it if it was present in
    the default configuration string, in the spirit of the above convention.  It
    also 'logs' the error in the 'error' option of the same section, if any OS
    exception occurred while opening or reading the configuration file.

    Args:
        cfg_dflt_string (string): represents the default configuration.
        cfg_filepath (string): the path of the configuration file; it is used 'as is'
            and if it is relative there is no guarantee of where it will actually point.

    Returns:
        ConfigParser.RawConfigParser object: object loaded with the parameters.
    '''

    # Load the default configuration
    cfg_dflt = ConfigParser.RawConfigParser(allow_no_value=True)
    cfg_dflt.readfp(io.BytesIO(cfg_dflt_string)) # should not throw any errors

    try:
        with open(cfg_filepath, 'r') as file_handle:
            cfg_file = ConfigParser.RawConfigParser()
            cfg_file.readfp(file_handle)
    except (OSError, IOError) as err:
        # 'log' the error in the ConfigParser object, if possible
        try: cfg_dflt.set('CONFIG', 'error', ''.join(('Error <', str(err),
                                                      '> with log file <', cfg_filepath, '>.')))
        except ConfigParser.NoSectionError: pass
        # return the default configuration as there was a problem reading the file
        return cfg_dflt
    # 'merge' it with the default configuration
    for section in cfg_dflt.sections():
        if cfg_file.has_section(section):
            for option in cfg_dflt.options(section):
                if cfg_file.has_option(section, option):
                    cfg_dflt.set(section, option, cfg_file.get(section, option))
    # Deal with the [INTERFACE] section now
    if cfg_file.has_section('INTERFACE'): # frankly if it doesn't there is a problem...
        for option in cfg_file.options('INTERFACE'):
            cfg_dflt.set('INTERFACE', option, cfg_file.get('INTERFACE', option))
    # Create or overwrite the 'location' option in section [CONFIG] if the section exists.
    location = os.path.realpath(file_handle.name)
    try: cfg_dflt.set('CONFIG', 'location', location)
    except ConfigParser.NoSectionError: pass

    return cfg_dflt
