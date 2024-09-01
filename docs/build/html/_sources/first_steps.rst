===========
First steps
===========

Let's test the Python client.

1. Setup Motive to track at least one rigid body.
2. Run one of the examples

   .. code-block:: console
   
      $ python3 examples/client_async.py
   
      [YYYY-mm-DD HH:MM:SS] INFO: Opening command socket on 0.0.0.0
      [YYYY-mm-DD HH:MM:SS] INFO: Discovering servers (number=1)
      [YYYY-mm-DD HH:MM:SS] INFO: Discovered 1 servers
      [YYYY-mm-DD HH:MM:SS] INFO: Connected to server XXX.XXX.XXX:1510
      [YYYY-mm-DD HH:MM:SS] INFO: Performing initial clock sync 0 ...
      [YYYY-mm-DD HH:MM:SS] INFO: Initial clock sync done: min_rtt NS ns, beta 0.0, delta NS
      [YYYY-mm-DD HH:MM:SS] INFO: Opening data unicast socket on 0.0.0.0:1511
      [YYYY-mm-DD HH:MM:SS] INFO: @NS:
      [YYYY-mm-DD HH:MM:SS] INFO: <NAME>, True, 1.0E-04: (1.1, 2.2, 3.3), (0.5, 0.5, 0.5, 0.5)
      [...]
      [YYYY-mm-DD HH:MM:SS] INFO: Unconnecting server ...
      [YYYY-mm-DD HH:MM:SS] WARNING: Data socket closed
      [YYYY-mm-DD HH:MM:SS] INFO: Unconnected
      [YYYY-mm-DD HH:MM:SS] INFO: Closing client ...
      [YYYY-mm-DD HH:MM:SS] WARNING: Command socket closed
      [YYYY-mm-DD HH:MM:SS] INFO: Closed


3. or the interactive CLI

   .. code-block:: console
   
      $ natnet_cli
   
      NatNet Client CLI. Type help or ? to list commands.
   
      (natnet) help
   
      Documented commands (type help <topic>):
      ========================================
      connect  data  delay  describe  disconnect  discover  help  log_level  quit
