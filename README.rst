.. README for mqttgateway

.. old text
  Full documentation is `here <http://mqttgateway.readthedocs.io/>`_.

**⚠ After a 2 years pause, it's finally back... 😀**

I am working on the new version.
 
######################
Welcome to mqttgateway
######################

``mqttgateway`` is a python framework to build consistent gateways to MQTT networks.

What it does:
=============

* it deals with all the boilerplate code to manage MQTT connections, load configuration
  and other data files, and create log handlers;
* it encapsulates the interface in a class that needs only 2 methods, an initialisation method
  (``__init__``) and a loop method (``loop`` or ``loop_start``);
* it creates an intuitive messaging abstraction layer between the wrapper and the interface;
* it isolates the syntax and keywords of the MQTT network from the interface.

Who is it for:
==============

Developers of MQTT networks in a domestic environment looking to adopt a definitive syntax for
their MQTT messages and to build gateways with their devices that are not MQTT enabled.

Available interfaces
====================

Check the existing fully developped interfaces.  Their names usually follows the
pattern **<interface_name>2mqtt**, for example
`musiccast2mqtt <https://musiccast2mqtt.readthedocs.io/>`_.

This library comes with a **dummy** interface to test the installation and that can be used
as a template.

..
  - **C-Bus**: gateway to the Clipsal-Schneider C-Bus system, via its PCI Serial Interface.

Links
=====

- **Documentation** on `readthedocs <http://mqttgateway.readthedocs.io/>`_.
- **Source** on `github <https://github.com/ppt000/mqttgateway>`_.
- **Distribution** on `pypi <https://pypi.org/project/mqttgateway/>`_.
