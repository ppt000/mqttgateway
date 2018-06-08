.. originally copied from mqtt_gateways documentation,
   Finished review by Paolo on 23 May 2018

########
Concepts
########

The message model
=================

The primary use case for this project is a domestic environment
with multiple devices of any type: lights, audio video components,
security devices, heating, air conditioning, controllers, keypads, etc...
For many (good) reasons, MQTT has been selected as the communication
protocol. But only a few, if any, devices are MQTT enabled.
For those that are not, there is a need to develop ad-hoc gateways to *bridge*
whatever interface they use natively (serial for example) to one that is MQTT based.
Even for those devices that communicate natively through MQTT, there is a need to agree on a
syntax that makes the exchange of messages coherent.

Example
-------

In the example below, a smart home has some lighting connected
in four different rooms through a proprietary network, four audio-video
devices connected through another proprietary network, and some
other devices that are already MQTT-enabled, but which still need
to speak a common language.

.. image:: domestic_iot.png
   :scale: 50%
   :align: center
   :alt: Diagram of a smart home with some connected devices

One of the objectives of this project is not only to define a common
MQTT syntax, but also to make it as *intuitive* as possible.  Ideally,
a human should be able to write an MQTT message off-hand and operate
successfully any device in the network.

Message Addressing
------------------

The first step of any message is to define its destination.  A flexible
addressing model should allow for a heuristic approach based on a
combination of characteristics of the recipient, on top of the
standard deterministic approach (e.g. a unique device id).
Four characteristics are usually considered:

- the **function** of the device: lighting, security, audio-video, etc;
- its **location**;
- its **gateway**: which application is managing that device, if any;
- the name of the **device**.

In our example, the MQTT point of view shows how those four characteristics, or just a subset,
can define all the devices in the network.

.. image:: iot_parameters.png
   :scale: 50%
   :align: center
   :alt: Diagram of a smart home from the MQTT network point of view

Some considerations about those four characteristics:

- not all four characteristics need to be provided to address succesfully
  a device;
- the **device** name can be generic (e.g. ``spotlight``) or specific and unique
  within the network (e.g. ``lightid1224``); in the generic case, obviously
  other characteristics are needed to address the device.
- any device can have more than one value for each characteristics,
  particularly the **function** and **device** ones (it is probable
  that the **gateway** and the **location** characteristics are unique for a given device);
- the **location** is important and probably the most intuitive characteristic
  of all; preferably it should represent the place where the device
  operates and not where it is physically located (e.g. an audio amplifier
  might be in the basement but it powers speakers in the living room;
  the location should be the living room); but the location might even not be
  defined (e.g. to address the security system of the whole house, or an audio
  network player that can broadcast to different *channels* or *zones*).
- the **gateway** is the most deterministic characteristic (alongside a unique
  device id); this should be the chosen route for fast and unambiguous
  messaging.
- the **function** is another important intuitive characteristic; not only it
  helps in addressing devices (combined with a location for example), but
  it also clarifies ambiguous commands (e.g. ``POWER_ON`` with ``lighting``
  or with ``audiovideo`` means different things). However things can get
  more complicated if a device has more than one function; this should be
  allowed, it is up to the gateway to make sure any ambiguity is resolved
  from the other characteristics.

Those four characteristics should ensure that the messaging model
is flexible enough to be heuristic or deterministic.  A gateway
will decide how flexible it wants to be.  If it has enough *processing bandwidth*,
it can decide to subscribe to all **lighting** messages for example, and then parse
all messages received to check if they are actually addressed to it.
Or it can subscribe only to messages addressed specifically to itself
(through the gateway name for example), restricting access only to the senders that
know the name of that gateway.

Message Content
---------------

The content of a message in the context of domestic IoT can be modelled
in many different ways.  This project splits it into 3 *characteristics*:

- a **type** with 2 possible values: *command* for messages that are requiring
  an action to be performed, or *status* for messages that only broadcast
  a state;
- an **action** that indicates what to do or what the status is referring to;
- a set of **arguments** that might complete the **action** characteristic.

The key characteristic here is the **action**, a string representing the *what* to do,
with the optional **arguments** helping to define by *how much* for example.
It can be ``POWER_ON`` and ``POWER_OFF`` on their own for example (no argument), or
``SET_POWER`` with the argument ``power:ON`` or ``power:OFF``, or both.
The interface decides what actions it recognises, the more the better.

Message Source
--------------

The sender, which can be a device or another gateway for example, is
an optional characteristic in our message model.  It can be very useful in
answering status requests in a targeted way, for example.

Bridging MQTT and the interface
===============================

There are therefore a total of 8 characteristics in our message model:

- **function**,
- **gateway**,
- **location**,
- **device**,
- **type**,
- **action**,
- **argument** of action,
- **sender**.

They are all strings except **type** which can only have 2 predefined values.
They are all the fields that can appear in a MQTT message, either in the topic or in the payload.
They are all attributes of the internal message class that is used to exchange
messages between the library and the interface being developed.
They are all the characteristics available to the developer to code its interface.

The internal message class
--------------------------

The internal message class :class:`internalMsg` defines the message objects stored
in the lists that are shared by the library and the interface.  There is a list for incoming
messages and a list for outgoing messages.
At its essence, the library simply parses MQTT messages into internal ones, and back.
The library therefore defines the MQTT syntax by the way it converts the messages.

The conversion process
-----------------------

The conversion process happens inside the class :class:`msgMap` with the
methods :meth:`MQTT2Internal` and :meth:`Internal2MQTT`.  These methods
achieve 2 things:

- define the syntax of the MQTT messages in the way the various
  characteristics are positioned within the MQTT topic and payload;
- if mapping is enabled, map the keywords for every characteristic between
  the MQTT *vocabulary* and the internal one; this is done via dictionaries initialised by a
  *mapping file*.

The MQTT syntax
---------------

The library currently defines the MQTT syntax as follows.
The topic is structured like this:

.. code-block:: none

	root/function/gateway/location/device/source/type

where ``root`` can be anything the developer wants (``home`` for example)
and ``type`` can be only ``C`` or ``S``.

The payload is simply the action alone if there are no arguments:

.. code-block:: none

	action_name

or the action with the arguments all in a JSON string like this:

.. code-block:: none

	{"action":"action_name","arg1":"value1","arg2":"value2",...}

where the first ``action`` key is written as is and the other argument keys
can be chosen by the developer and will be simply copied in the **argument**
dictionary.

This syntax is defined within the 2 methods doing the conversions.  The rest of the library
is agnostic to the MQTT syntax.  Therefore one only needs to change these 2 methods to change
the syntax.  However in that case, all the devices and other gateways obviously have to
adopt the same new syntax.

The mapping data
----------------

By default, when the mapping option is disabled, the keywords used in the MQTT messages
are simply copied in the internal class.  So, for example, if the **function** in the MQTT
message is ``lighting``, then the attribute ``function`` in the :class:`internalMsg` will also
be ``lighting``.
If for any reason a keyword has to change on either *side*, it has to be reflected on the other
one, which is unfortunate.  For example, let's assume a location name in the MQTT vocabulary is ``basement`` and that is what is used in the internal code of the interface to start with. For
some reason the name in the MQTT vocabulary needs to be changed to ``lowergroundfloor``.
In order for the interface to recognise this new keyword, a mapping can be introduced that links
the keyword ``lowergroundfloor`` in the MQTT messages to ``basement`` in the internal
representation of messages.  This mapping is defined in a separate JSON file, and the code does
not need to be modified.

The mapping option can be enabled (it is off by default) in the configuration file, in which
case the location of the JSON file is required.
All the keyword characteristics (except **type**) can (but do not have to) be mapped in that file:
**function**, **gateway**, **location**, **device**, **sender**, **action**, **argument keys** and
**argument values**.
To give more flexibility, there are 3 mapping options available for each characteristic that need
to be specified:

- ``none``: the keywords are left unchanged, so there is no need to provide
  the mapping data for that characteristic;
- ``strict``: the conversion of the keywords go through the provided map,
  and any missing keyword raises an exception; the message with that keyword is probably ignored;
- ``loose``: the conversion of the keywords go through the provided map,
  but missing keywords do not raise any error but are passed unchanged.

The mapping between internal keywords and MQTT ones is a one-to-many relationship
for each characteristic.  For each internal keyword there can be more than one MQTT keyword,
even if there will have to be one which has *priority* in order to define without ambiguity
the conversion from internal to MQTT keyword.  In practice, this MQTT keyword will be the
first one in the list provided in the mapping (see below) and the other keywords of that list
can be considered *aliases*.  Going back to the example above, for the unique internal location
keyword ``basement``, we could define a list of MQTT keywords as
``["lowergroundfloor", "basement"]``, so that ``basement`` in internal code gets converted
to ``lowergroundfloor`` in MQTT (as it is the new *official* keyword) but ``basement`` in
MQTT is still accepted as a keyword that gets *converted* to ``basement`` in internal messages.

In practice, the mapping data is provided by a JSON formatted file.  The JSON
schema ``mqtt_map_schema.json`` is available in the ``gateway`` package.
New JSON mapping files can be tested against this schema (I use the online
validation tool https://www.jsonschemavalidator.net/)
The mapping file also contains the topics to subscribe to and the root token
for all the topics.  These values override the ones found in the configuration file
if the mapping feature is enabled.
