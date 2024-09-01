===========
Executables
===========

The package contains two helper script to interact with the NatNet server


Discover
========

Discover NatNet server in the local network

.. argparse::
   :module: natnet_py.natnet_discover
   :func: parser
   :prog: natnet_discover

Example
~~~~~~~

.. code-block:: console


   $ natnet_discover       
   ------------------------------------------------------------
   127.0.0.1:1510
       python_natnet server using NatNet version 3.1.0.0
       unicast data stream on :1511
   ------------------------------------------------------------


Interactive shell 
=================

Interact with NatNet servers

.. argparse::
   :module: natnet_py.natnet_cli
   :func: parser
   :prog: natnet_cli


Example
~~~~~~~

.. code-block:: console

   $ natnet_cli

   NatNet Client CLI. Type help or ? to list commands.

   (natnet) help

   Documented commands (type help <topic>):
   ========================================
   connect  data  delay  describe  disconnect  discover  help  log_level  quit
 
   (natnet) log_level INFO

   (natnet) connect 127.0.0.1
   
   [...] INFO: Opening command socket on 0.0.0.0
   [...] INFO: Connecting to 127.0.0.1 ...
   [...] INFO: Connected to server 127.0.0.1:1510
   [...] INFO: Performing initial clock sync 0 ...
   [...] INFO: Initial clock sync done: min_rtt 245000 ns, beta 0.0, delta 1725205710334906000
   [...] INFO: Opening data unicast socket on 0.0.0.0:1511

   (natnet) quit

   [...] INFO: Closing client ...
   [...] WARNING: Data socket closed
   [...] WARNING: Command socket closed
   [...] INFO: Closed

Dump 
====

Saves all rigid body data to HDF5.

.. argparse::
   :module: natnet_py.natnet_dump
   :func: parser
   :prog: natnet_dump

For each rigid_body, it creates the following datasets, containing the mocap updates:

- ``/rigid_bodies/<NAME>/error``: residual error in mm       
- ``/rigid_bodies/<NAME>/orientation``: orientation quaternions (x, y, z, w)   
- ``/rigid_bodies/<NAME>/position``: positions in mm (x, y, z)   
- ``/rigid_bodies/<NAME>/time``: capture time stamp in ns (time since epoch)        
- ``/rigid_bodies/<NAME>/tracked``: whether the rigid body is tracked (bool)    

If a duration is not provided, stop the data collection by killing the process. 

Example
~~~~~~~

.. code-block:: console

   $ natnet_dump my_file.h5 --duration 10

   [...] INFO: Opening command socket on 0.0.0.0
   [...] INFO: Discovering servers (number=1)
   [...] INFO: Discovered 1 servers
   [...] INFO: Connected to server 192.168.1.109:1510
   [...] INFO: Performing initial clock sync 0 ...
   [...] INFO: Initial clock sync done: min_rtt 137000 ns, beta 0.0, delta 1725205710334936500
   [...] INFO: Opening data unicast socket on 0.0.0.0:1511
   [...] INFO: Collecting data ...
   [...] INFO: Closing client ...
   [...] WARNING: Data socket closed
   [...] WARNING: Command socket closed
   [...] INFO: Closed
   [...] INFO: Collected data
   [...] INFO: Saving data to my_file.h5 ...
   [...] INFO: Saved data


   $ h5ls -r my_file.h5
   /                             Group
   /rigid_bodies                 Group
   /rigid_bodies/rb0             Group
   /rigid_bodies/rb0/error       Dataset {32}
   /rigid_bodies/rb0/orientation Dataset {32, 4}
   /rigid_bodies/rb0/position    Dataset {32, 3}
   /rigid_bodies/rb0/time        Dataset {32}
   /rigid_bodies/rb0/tracked     Dataset {32}
   /rigid_bodies/rb1             Group
   /rigid_bodies/rb1/error       Dataset {32}
   /rigid_bodies/rb1/orientation Dataset {32, 4}
   /rigid_bodies/rb1/position    Dataset {32, 3}
   /rigid_bodies/rb1/time        Dataset {32}
   /rigid_bodies/rb1/tracked     Dataset {32}


GUI 
===

A very basic web-based 2D GUI to display MoCap updates

.. argparse::
   :module: natnet_py.natnet_gui
   :func: parser
   :prog: natnet_gui

It will open a web-browser where it draws rigid bodies on a map 
and display their poses in a table.


Example
~~~~~~~

.. code-block:: console

   $ natnet_gui

.. image:: gui.png