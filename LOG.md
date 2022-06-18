# LOG of MQTTGATEWAY

## [17 June 2022]

Start Version 2.0 of this library.

### Objectives
- simplify the startup process: loading of configuration, logging setup, etc...
- adapt logging to simultaneous multiple sessions.
- change multi threading to async.

### Inputs

The library has to facilitate the retrieval of the 2 files needed for any application using
this library:
- the configuration file,
- the mapping file.

These are stored in files with possibly different names, possibly in different folders.

To start with and make it simple, assume the location of those files is
in a sub-directory of the home directory called `.mqttgtw` (for example).
Assume as well that those 2 files have the same name of the application,
with respectively the suffixes `cfg` and `json`.
Add the possibility of defining another configuration file on the command line
with the option `-c`, which has to be located in the same directory though.

### Logs

The library has to facilitate the logging of several concurrent application
all using the same library but obviously running other applications.

Propose only 3 different handlers:
- the console, mostly for development,
- rotating file on local system,
- journalmd compatible logging (if available).

For the rotating files, use a pre-defined main folder in the home directory,
for example `mqttgtw_logs`, and create a sub-folder there for each application running.




Also to make it simple, start by locating 


