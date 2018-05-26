.. mqttgateway documentation master file, created by
   sphinx-quickstart on Wed May 16 18:13:24 2018.

.. originally copied from mqtt_gateways documentation,
   reviewed by Paolo on 22 May 2018

#######################################
Welcome to mqttgateway's documentation!
#######################################

``mqttgateway`` is a python wrapper to build consistent gateways to an MQTT network.

.. image:: basic_diagram.png
   :scale: 30%
   :align: right

What it does:
=============

* it deals with all the boilerplate code to manage an MQTT connection, load configuration
  and other data files, and create log handlers,
* it encapsulates the interface in a class that needs only 2 methods ``__init__`` and ``loop``,
* it creates an intuitive messaging abstraction layer between the wrapper and the interface,
* it can isolate the syntax and keywords of the MQTT network from the internal ones of the interface.

Who is it for:
==============

Developers of MQTT networks in a domestic environment looking to adopt a definitive syntax for their MQTT messages and to build gateways with their devices that are not MQTT enabled.

Available interfaces
====================

Check in the related repos some fully developped interfaces.  Their names usually follows the
pattern **<interface_name>2mqtt**, for example **musiccast2mqtt**.

This library comes with 2 interfaces:

- **dummy**: the template; check the :mod:`mqttgateway.dummy` documentation.
- **entry**: example used for the :doc:`tutorial <tutorial>`.

Contents
========

.. toctree::
   :maxdepth: 2
   :numbered:

   Overview <overview>
   Installation <installation>
   Concepts <concepts>
   Tutorial <tutorial>
   Configuration <configuration>
   Project Description <description>
   Package Documentation <mqttgateway_package>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
