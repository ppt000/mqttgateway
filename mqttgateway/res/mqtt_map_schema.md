Schema for Map Files
====================

Map files are used by the application to configure the MQTT messages.
The bulk of the information in a table between constants used in the application code and tokens used in the MQTT messages to describe the same thing (location, function, etc...).

Map files are in JSON format.

The constant defining something in the application is unique, but it is possible to have more than one MQTT token to describe the same thing out of convenience (for example in the case of a location, `LIVING_ROOM` could be the constant used in the code, and the MQTT tokens to represent it could be `living_room` or `living`).  Therefore the map data will have for each constant a name/value pair made of the constant in the code and an array of strings (the MQTT tokens).

The main *object* has 10 name/value pairs:

- `"root"`: (*string*) the string representing the root of all the MQTT messages.
- `"topics"`: (*array*) the list of topics that the application will have to subscribe to; it can contain wildcards.
- `"function"`, `"gateway"`, `"location"`, `"device"`, `"sender"`, `"action"`, `"argkey"`, `"argvalue"`: the values associated with these names are all objects with the same format, let's call it the *map object*.

A map object has at most 2 name/value pairs:

- `"maptype"`: (*string*) can only be one of `"none"`, `"loose"`, `"strict"`.  If the value is `"none"`, then the object stops here.
- `"map"`: (*object*) a set of name/value pairs where the name is the constant used in the application code, and the value is an array of strings of all the tokens that can represent that constant in the messages.

Validation
----------
The requirements for the file to be valid (and that should be checked by the application) are:
- the 10 names of the main object are present,
- the values for each name are in the format expected,
- each map is consistent, in particular there are never duplicates in the list of tokens.

Example
-------

```
{
    "root": "oer",
    "topics": ["oer/security/+/frontgarden/+/+/C",
                "oer/+/entry2mqtt/+/+/+/C",
                "oer/+/+/+/gate/+/C"],
    "function": {
        "maptype": "strict",
        "map": {
            "": [""],
            "Security": ["security"],
            "Lighting": ["lighting"]
        }
    },
    "gateway": {
        "maptype": "strict",
        "map": {
            "": [""],
            "cbus": ["cbus"],
            "siedle": ["siedle"]
        }
    },
    "location": {
        "maptype": "strict",
        "map": {
            "": [""],
            "gate_entry": ["front_entry"]
        }
    },
    "device": {
        "maptype": "strict",
        "map": {
            "": [""],
            "Gate": ["gate"],
            "LightButton": ["lightbutton"]
        }
    },
    "sender": {
        "maptype": "none"
    },
    "action": {
        "maptype": "strict",
        "map": {
            "LIGHTBUTTON_ON": ["lightbutton_on"],
            "LIGHTBUTTON_OFF": ["lightbutton_off"],
            "GATE_OPEN": ["gate_open"],
            "LIGHT_OFF": ["light_off"],
            "LIGHT_ON": ["light_on"],
            "GATE_CLOSE": ["gate_close"]
        }
    },
    "argvalue": {
        "maptype": "none"
    },
    "argkey": {
        "maptype": "none"
    }
}
```

