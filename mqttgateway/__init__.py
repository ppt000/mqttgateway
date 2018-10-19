''' Root package for the **mqttgateway** library.

The library has 4 sub-packages:

* ``gateway``: the core of the library;
* `` utils``: the utilities used by the core package;
* ``dummy``: an empty interface to help starting a new interface;
* ``entry``: the example interface.

Only ``gateway`` and ``utils`` are needed to run the library.

.. TODO: Separate the ``dummy`` and ``entry`` sub-packages in an ``examples`` package.
'''

__version_info__ = (1, 0, 0)
__version__ = '.'.join(str(c) for c in __version_info__)