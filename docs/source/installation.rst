.. REVIEWED 9 November 2018

############
Installation
############

Download
========

Get the library from the PyPi repository with the ``pip`` command, preferably using the ``--user`` option:

.. code-block:: none

    pip install --user mqttgateway

Alternatively use the *bare* ``pip`` command if you have administrator rights or if you are in a
virtual environment.

.. code-block:: none

    pip install mqttgateway

Running ``pip`` also installs an executable file (``exe`` in Windows or executable python
script in Linux) called ``dummy2mqtt``.  It launches the demo interface **dummy** with the
default configuration. Its location *should* be ``%APPDATA%\Python\Scripts\dummy2mqtt.exe``
on Windows and ``~/.local/bin/dummy2mqtt`` on Linux
(*it probably depends on the distribution though...*).
If not, please search for the file manually.

Also, those same locations *should* be already defined in the **PATH** environment variable and
therefore the executable *should* launch from any working directory.  If not, the variable will
have to be updated manually, or the executable needs to be specified with its real path.

Configuration
=============

A configuration file is needed for each interface.  In the library, the default interface ``dummy``
has its own configuration file ``dummy2mqtt.conf`` inside the package folder.

The configuration file has a standard ``INI`` syntax, as used by the standard library
``ConfigParser`` with sections identified by ``[SECTION]`` and options within sections identified
by ``option:value``.  Comments are identified with a starting character ``#``.

There are four sections:

#. ``[MQTT]`` defines the MQTT parameters, most importantly the IP address of the broker
   under the option ``host``.
   The address of the MQTT broker should be provided in the same format
   as expected by the **paho.mqtt** library, usually a raw IP address
   (``192.168.1.55`` for example) or an address like ``test.mosquitto.org``.
   The default port is 1883, if it is different it can also be indicated
   in the configuration file under the option ``port``.
   Authentication is not available at this stage.

#. ``[LOG]`` defines the different logging options.  The library can log to the console,
   to a file, send emails or just send the logs to the standard error output.
   By default it logs to the console.

#. ``[INTERFACE]`` is the section reserved to the actual interface using this library.
   Any number of options can be inserted here and will be made available to the interface
   code through a dictionary initialised with all the ``option:value`` pairs.

#. ``[CONFIG]`` is a section reserved to the library to store information about the configuration
   loading process.  Even if it is not visible in the configuration file it is created at runtime.

For more details about the ``.conf`` file, its defaults and the command line arguments,
go to :doc:`Configuration <configuration>`.

Launch
======

If ``pip`` installed correctly the executable files, just launch it from anywhere:

.. code-block:: none

    dummy2mqtt

By default, the process will log messages from all levels into the console.
It should start logging a banner message to indicate the application has started,
then a list of the full configuration used.

If the MQTT connection is successful it should say so as well as
displaying the topics to which the application has subscribed.

After the start-up phase, the **dummy** interface logs (at a DEBUG level)
any MQTT messages it receives.  It also emits a unique message every 30 seconds.
Start your favourite MQTT monitor app (I use the excellent
`mqtt-spy <https://kamilfb.github.io/mqtt-spy/>`_).
Connect to your MQTT broker and subscribe to the topic:

.. code-block:: none

	home/+/dummy/+/+/+/C

You should see the messages arriving every 30 seconds in the MQTT monitor,
as well as in the log.

Publish now a message from the MQTT monitor:

.. code-block:: none

	topic: home/lighting/dummy/office/undefined/me/C
	payload: LIGHT_ON

You should see in the log that the message has been received
by the gateway, and that it has been processed correctly, meaning that
even if it does not do anything, the translation methods have worked.

The mapping data
================

The mapping data is an optional feature that allows to map some or every keyword in the
MQTT vocabulary into the equivalent keyword in the interface.
This mapping is a very simple many-to-one relationship between MQTT and internal keywords
for each characteristic,
and its use is only to isolate the internal code from any changes in the MQTT vocabulary.

For the **dummy** interface, the mapping data is provided by the text file
``dummy_map.json``.  It's just there as an example, and actually is disabled by default.
To enable it, change the configuration file accordingly and test the mapping with the MQTT
monitor app.  If you send MQTT messages with MQTT keywords from the mapping file, you should
see their *translation* in the logs.

Note that the map file also contains the *root* of the MQTT messages and the topics that the
interface should subscribe to.

For more details on the mapping data, go to :doc:`Description <description>`.

Deploying a gateway
===================

The objective of developing a gateway is to ultimately deploy it in a production environment.
To install a gateway as a service on a linux machine, go to :doc:`Configuration <configuration>`.
