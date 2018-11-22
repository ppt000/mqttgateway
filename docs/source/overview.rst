.. REVIEWED 9 November 2018

########
Overview
########

Objective
=========

When setting up an IoT eco-system with a lot of different
devices, it becomes quickly difficult to have them talking to each other.
A few choices need to be made to solve this problem.
This project assumes that one of those choices has been made: using
`MQTT <http://mqtt.org/>`_ as the messaging transport.
This project then intends to help in the next set of choices to make:
defining a messaging model and expressing it in an MQTT syntax to be shared by all devices.

This model is implemented as a python library aimed at facilitating coding the gateways
between devices that do not support natively MQTT communication and the MQTT network.
These gateways can then run as services on machines connected to these
devices via whatever interface is available: serial, Bluetooth, TCP, or else.

.. image:: basic_diagram.png
   :scale: 50%

Description
===========

This project has two parts:

1. The definition of the messaging model.
   It is an abstraction layer that defines a message by a few characteristics, adapted to
   domestic IoT environments, that help resolving the destination and purpose of the
   message in a flexible and intuitive way.
2. The implementation of this model through a python library.
   The library takes care of formatting and translating back and forth the messages
   between their MQTT syntax and their internal representation, as well as managing
   the connection to the broker and various application necessities.

For more information, go to :doc:`Description <description>`.

Usage
=====

This project is provided with the core library,
and an example interface (the **dummy** interface) that does not
interface with anything but shows how the system works.
Once installed, running the application ``dummy2mqtt`` allows to test the basic
configuration and show how it is reacting to incoming MQTT messages, for example.

Developers can then write their own interface by using the **dummy** interface
as a template, or following the tutorial alongside the theoretical interface **entry**.

End users will download already developed interfaces, for which this library will simply
be a dependency.

For a complete guide on how to develop an interface, go to :doc:`Tutorial <tutorial>`.

Installation
============

The installation can be done with ``pip``, on both Linux and Windows systems.
The only dependency is the `paho.mqtt <https://pypi.python.org/pypi/paho-mqtt>`_ library.

For the full installation guide, go to :doc:`Installation <installation>`.
