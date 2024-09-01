# natnet_py
Pure Python NatNet client. See the documentation on https://jeguzzi.github.io/natnet_py.

## Installation

`pip install git+https://github.com/jeguzzi/natnet_py.git`

## Usage

The package contains two clients with very similar APIs (one offering an asyncronous interface based on `asyncio`, the other offering a blocking interface) to interact with a NatNet server (i.e., a Motive application). For example, using the bloicking interface, a minimal program that connect to a discoverable server and then fetch a single MoCap update is:

```python
   import natnet_py

   client = natnet_py.SyncClient()
   connected = client.connect(discovery_address="255.255.255.255")
   if connected:
       data = client.get_data()
   client.close()
```

## Related software

Have a look at https://github.com/jeguzzi/optitrack_ros_py for a ROS2 wrapper of this library.


