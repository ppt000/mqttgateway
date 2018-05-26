

######################
Welcome to mqttgateway
######################

``mqttgateway`` is a python wrapper to build consistent gateways to an MQTT network.

What it does:
=============

* it deals with all the boilerplate code to manage an MQTT connection, load configuration
  and other data files, and create log handlers,
* it encapsulates the interface in a class that needs only 2 methods ``__init__`` and ``loop``,
* it creates an intuitive messaging abstraction layer between the wrapper and the interface,
* it can isolate the syntax and keywords of the MQTT network from the internal ones of the interface.


Who is it for:
==============

Developers of MQTT networks in a domestic environment looking to adopt a definitive syntax for their
MQTT messages and to build gateways with their devices that are not MQTT enabled.


Available interfaces
====================

Check the existing fully developped interfaces.  Their names usually follows the
pattern **<interface_name>2mqtt**, for example
`musiccast2mqtt <https://musiccast2mqtt.readthedocs.io/>`_.

This library comes with 2 interfaces:

- **dummy**: the template; check the :mod:`mqttgateway.dummy` documentation.
- **entry**: example used for the :doc:`tutorial <tutorial>`.

..
  - **C-Bus**: gateway to the Clipsal-Schneider C-Bus system, via its PCI Serial Interface.

Links
=====

Documentation on `readthedocs <http://mqttgateway.readthedocs.io/>`_.
Source on `github <https://github.com/ppt000/mqttgateway>`_.
Distribution on `pypi <https://pypi.org/project/mqttgateway/>`_.