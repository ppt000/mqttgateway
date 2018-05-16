

The documentation in ``docs/source`` is formatted to be read in `ReadTheDocs <http://mqtt-gateways.readthedocs.io/>`_.
Head there to browse it.

Welcome to MQTT_Gateways
=========================

``mqtt_gateways`` is a python wrapper to build consistent gateways to MQTT networks.

.. image:: docs/source/basic_diagram.png
   :scale: 30%
   :align: right

What it does:
-------------

* it deals with all the boilerplate code to manage an MQTT connection,
  to load configuration and mapping data, and to create log handlers,
* it encapsulates the interface in a class that needs only 2 methods
  ``__init__`` and ``loop``,
* it creates an intuitive messaging abstraction layer between the wrapper
  and the interface,
* it isolates the syntax and keywords of the MQTT network from the internals
  of the interface.

Who is it for:
--------------

Developers of MQTT networks in a domestic environment, or *smart homes*,
looking to adopt a definitive syntax for their MQTT messages and
to build gateways with their devices that are not MQTT enabled.

Available gateways
------------------

The repository contains some already developed gateways to existing systems.
The currently available gateways are:

- **C-Bus**: gateway to the Clipsal-Schneider C-Bus system, via its PCI Serial Interface.
