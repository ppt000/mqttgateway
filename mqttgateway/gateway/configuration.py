'''
The default configuration settings in a single string constant.

Given how the configuration loader works, only the sections and options
declared already here will be considered in any external configuration file.
If an external configuration file is read and contains sections and options not
included in here, they will be ignored, except for the ``[INTERFACE]`` section.
The section ``[INTERFACE]`` is reserved to the configuration parameters that might be
needed by the interface being implemented.

Use this declaration as a template configuration file.
'''

CONFIG = '''
[CONFIG]
# Reserved section used by the loader to store the location where
#   the configuration settings are coming from, or to store
#   the error if there was one.

[INTERFACE]
# Section for whatever options are needed by the gateway interface
#   being developed. All these options will be written in a
#   dictionary and passed to the interface.

[MQTT]
# The parameters to connect to the MQTT broker
host: 127.0.0.1
port: 1883
keepalive: 60

# This is the timeout of the 'loop()' call in the MQTT library
timeout: 0.01

# Mapping option. By default it is off.
mapping: off

# Map file: there needs to be a mapping file if the <mapping> option is on.
#   If the <mapfilename> option is left blank, the mapping option is turned
#   off, whatever the value of the <mapping> option.
#   To use the default name and path, use a dot <.> for this option.
#   The default name used is <*application_name*.map>.
#   See below for other instructions on file names and paths.
mapfilename: .

# The 'root' keyword for all MQTT messages.
#   Only necessary if <mapping> is off, disregarded otherwise
#   as the keyword should then be found in the mapping file.
root: home

# The topics to subscribe to, separated by a comma.
#   Only necessary if <mapping> is off, disregarded otherwise
#   as the topics should then be found in the mapping file.
topics: home/dummyfunction/#, home/+/dummy/#

[LOG]
# Log file: all WARN level logs and above are sent to stderr or equivalent.
#   To log levels below that a file location is needed.
#   Leave this option blank to not enable a log file - and therefore logs
#   of level below WARN will be lost.
#   Use a dot <.> to use the default name and path.
#   The default name used is <*application_name*.log>.
#   Make sure the process will have the rights to write in this file.
#   See below for other instructions on file names and paths.
logfilename: .

# Turn debug 'on' if logging of all DEBUG level messages is required, otherwise its INFO
debug: off

# Console level: use NONE for no console output, otherwise the level wanted.
#   Logs will be directed to stdout.  Levels are the ones from the logging module:
#   CRITICAL, ERROR, WARN or WARNING, INFO and DEBUG.
consolelevel: NONE

# Email credentials; leave empty if not required.
#   All CRITICAL level logs are sent to this email, if defined.
#   For now there is no authentication, it is only here for 'internal' emails.
emailhost:
# for example: emailhost: 127.0.0.1
emailport:
# for example: emailport: 25
emailaddress:
# for example: address: me@example.com

#------------------------------------------------------------------------------
# Note on file paths and names:
#   - the default name is 'application_name' +
#                          default extension (.log, .map, ... etc);
#   - the default path is the 'application' directory, which 'should' be the
#     location of the launching script;
#   - file paths can be empty in which case the default name and path will be
#     used;
#   - file paths can be directory only (ends with a '/') and are appended with
#     the default name;
#   - file paths can be absolute or relative; absolute start with a '/' and
#     relative are prepended with the default directory;
#   - file 'paths' can be file only (no '/' whatsoever) and are prepended with
#     the default directory;
#   - use forward slashes '/' in any case, even for Windows systems, it should
#     work;
#   - however for Windows systems, use of the drive letter might be an issue
#     and has not been tested.
#------------------------------------------------------------------------------

'''