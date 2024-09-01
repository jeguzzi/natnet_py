============
Introduction
============

`Natnet <https://docs.optitrack.com/developer-tools/natnet-sdk>`_ is the protocol that clients uses to interact with Motive via udp sockets.
The official `implementation <https://optitrack.com/software/natnet-sdk/>`_ by Optitrack provide a compiled C++ shared library. The library is released together with examples for other programming languages where clients directly "depacketize" the messages. This package is based on such examples and the effort by the community (primary `python_natnet <https://github.com/mje-nz/python_natnet>`_) to reverse engineer Natnet.


This packages implements a pure Python Natnet client that you can use to configure Motive and receive data, e.g., the poses of tracked rigid bodies. It offers an asynchronous and a synchronous interface; both can be used to set up the typical client life cycle:

1. The client discovers the accessible motive instances.
2. The client connects to the chosen instance.
3. The client receives updates from the server.
4. The client closes the connection.


For examples, using the asynchronous interface, the life cycle can be implemented as

.. code-block:: python
    
   import natnet_py

   client = natnet_py.AsyncClient()
   connected = await client.connect(discovery_address=255.255.255.255)
   if connected:
       # read the first 10 updates
       for i in range(10):
           data = await client.get_data()
   await client.close()

while using synchronous interface, the equivalent program reads

.. code-block:: python
    
   import natnet_py

   client = natnet_py.SyncClient()
   connected = client.connect(discovery_address=255.255.255.255)
   if connected:
       # read the first 10 updates
       for i in range(10):
           data = client.get_data()
   client.close()


Clients have callbacks for received data, which you can use as

.. code-block:: python

   import natnet_py


   def my_callback(stamp_ns: int, msg: MoCapData) -> None:
       ...


   client = natnet_py.AsyncClient()
   connected = await client.connect(discovery_address=255.255.255.255)
   if connected:
       client.data_callback = my_callback
       await client.run(duration=2.0)    
   await client.close()


Moreover, clients can inspect Motive configuration and change some parameters.

.. code-block:: python

   import natnet_py


   client = natnet_py.AsyncClient()
   connected = await client.connect(
       server_address=127.0.0.1, start_listening_for_data=False)
   if connected:
       # Getting/Setting the framerate
       framerate = await client.get_framerate()
       _ = await client.set_framerate(60)
       # Getting/Setting the name of a rigid body
       name = await client.get_property(
           name=b"Name", node=b"1", kind=bytes)
       _ = await client.set_property(
           name=b"Name", value=b"my_name", node=b"1")
   await client.close()