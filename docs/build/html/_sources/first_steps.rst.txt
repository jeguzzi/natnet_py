===========
First steps
===========

Let's test the Python client.

1. Setup Motive to track at least one rigid body.
2. Run one of the examples

   .. code-block:: console
   
      $ python3 examples/client_async.py
   
      [STAMP] INFO: Connecting NatNet server ...
      [STAMP] INFO: Discovered servers: XXX.XXX.XXX.XXX:1510
      [STAMP] INFO: Got description for rigid bodies: rb0
      [STAMP] INFO: NatNet client connected to XXX.XXX.XXX.XXX:1510
      [STAMP] INFO: Creating data unicast socket on port 1511
      [STAMP] INFO: Start initial clock sync
      [STAMP] INFO: Connected NatNet server
      [STAMP] INFO: @STAMP_NS:
      [STAMP] INFO: rb0, True, 1.3E-04: (0.001, 0.015, 0.009), (-4.559e-04,    3.982e-04, 5.767e-04, -1.000e+00)
      [STAMP] INFO: @STAMP_NS:
      [STAMP] INFO: rb0, True, 1.6E-04: (0.001 +0.015 -0.009), (5.695e-04,    1.975e-04, 8.105e-04, -1.000e+00)
      [...]
      [STAMP] INFO: Unconnecting NatNet server ...
      [STAMP] WARNING: Data socket closed
      [STAMP] WARNING: Command socket closed
      [STAMP] INFO: Unconnected
      [STAMP] INFO: Unconnected NatNet server

3. or the interactive CLI

   .. code-block:: console
   
      $ natnet_cli
   
      NatNet Client CLI. Type help or ? to list commands.
   
      (natnet) help
   
      Documented commands (type help <topic>):
      ========================================
      connect  data  delay  describe  disconnect  discover  help  log_level  quit
