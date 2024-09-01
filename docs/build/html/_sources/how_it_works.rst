============
How it works
============

We give a short overview of Motive client/server architecture based on NatNet. Please refer to the `official Optitrack documentation <https://docs.optitrack.com>`_ for more information.


Discovery
=========

Motive listen to the command port (by default set to 1510) for clients.
When a client announce itself sending a :py:class:`discovery request <natnet_py.protocol.DiscoveryRequest>`, it sends back :py:class:`information about itself <natnet_py.protocol.ServerInfo>` containing the data port, the protocol version, and possibly the multicast address.
If the clients already knows the server address, it can directly connect to it.

Call :py:meth:`natnet_py.AsyncClient.discover` or :py:meth:`natnet_py.SyncClient.discover` to discover all reachable hosts. You can limit discovering to a specific network.

Connection
==========

To connect to a server, the client needs to know its address. Then, it can send a :py:class:`connection request <natnet_py.protocol.ConnectRequest>` and get back the same :py:class:`server information <natnet_py.protocol.ServerInfo>` from discovery.

Call :py:meth:`natnet_py.AsyncClient.connect` or :py:meth:`natnet_py.SyncClient.connect` to connect to a server.


Streaming
=========

Once connected, the client receives a stream of :py:class:`mocap updates <natnet_py.protocol.MoCapData>` (with the pose of all tracked rigid bodies and so on) through a udp socket. This socket may use multicast or unicast, depending on how Motive is configured. The server supports multiple client at once: when unicasting, the same messages is sent multiple time, one for each client.


Clock
=====

You can let the python client synchronize the clock with the Motive server, right after connection, by specifying ``sync=True`` in the :py:class:`constructor <natnet_py.AsyncClient.__init__>`. 
Server and client clocks are synchronized by exchanging multiple echo messages (:py:meth:`natnet_py.protocol.EchoRequest` -> :py:meth:`natnet_py.protocol.EchoResponse`). 

The mocap data is stamped by the server in :py:class:`natnet_py.protocol.FrameSuffixData`. If synchronized, you can convert server ticks to client time using :py:meth:`natnet_py.AsyncClient.server_ticks_to_client_ns_time`. 

