============
Internal API
============

.. autoclass:: natnet_py.protocol.Version
   :members:
   :undoc-members:
   :exclude-members: __init__, pack, unpack

Requests
========

Echo
~~~~

Request
-------

.. autoclass:: natnet_py.protocol.EchoRequest
   :members:
   :exclude-members: __init__, pack, unpack

Response
--------

.. autoclass:: natnet_py.protocol.EchoResponse
   :members:
   :exclude-members: __init__, pack, unpack

Discovery
~~~~~~~~~

Request
-------

.. autoclass:: natnet_py.protocol.DiscoveryRequest
   :members:
   :exclude-members: __init__, pack, unpack

Response
--------

.. autoclass:: natnet_py.protocol.ServerInfo
   :members:
   :exclude-members: __init__, pack, unpack

.. autoclass:: natnet_py.protocol.ConnectionInfo
   :members:
   :exclude-members: __init__, pack, unpack

Connection
~~~~~~~~~~

Request
-------

.. autoclass:: natnet_py.protocol.ConnectRequest
   :members:
   :exclude-members: __init__, pack, unpack

Response
--------

:py:class:`natnet_py.protocol.ServerInfo`.

