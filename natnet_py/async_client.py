import socket
import logging
import asyncio
import struct
import time

from . import protocol
from . import clock

from typing import Any, Callable, TypeVar, Type, cast

T = TypeVar("T")
CmdDataCallback = Callable[[protocol.MoCapData], None]
DataCallback = Callable[[int, protocol.MoCapData], None]
DoneCallback = Callable[[], None]
DataQueue = asyncio.Queue[tuple[int, protocol.MoCapData]]
ResponseCallback = Callable[[Any, tuple[str, int]], None]


def tokenize(*tokens: bytes) -> bytes:
    return b",".join(filter(None, tokens))
    # return b",".join(tokens)


class DataProtocol(asyncio.Protocol):
    def __init__(
        self,
        membership: bytes,
        cb: CmdDataCallback,
        done: asyncio.Future[None],
        logger: logging.Logger,
    ):
        self._membership = membership
        self._done = done
        self._cb = cb
        self.logger = logger
        self.logger.debug("Data socket initialized")

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        # sock = transport.get_extra_info("socket")
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
        #                 self._membership)
        self.logger.debug("Data socket connected")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        # print('datagram_received', data, addr)
        msg = protocol.unpack(protocol.Buffer(data))
        if isinstance(msg, protocol.MoCapData):
            self._cb(msg)

    def error_received(self, exc: Any) -> None:
        self.logger.error(f'{exc}')

    def connection_lost(self, exc: Any) -> None:
        self.logger.warning("Data socket closed")
        self._done.set_result(None)


class CommandProtocol(asyncio.Protocol):
    def __init__(
        self,
        address: str,
        port: int,
        cb: CmdDataCallback,
        connected: asyncio.Future[None],
        done: asyncio.Future[None],
        logger: logging.Logger,
    ):
        self._server = (address, port)
        self._response_type: Any = None
        self._response_cb: dict[Any, ResponseCallback] = {}
        self._keep_alive_task: asyncio.Task[None] | None = None
        self._keep_alive_msg = protocol.pack(protocol.KeepAliveRequest())
        self._cb = cb
        self._done = done
        self._connected = connected
        self._keep_alive = False
        self.keep_alive_timeout = 5.0
        self.logger = logger
        self.logger.debug("Command socket initialized")

    @property
    def address(self) -> str:
        return self._server[0]

    @address.setter
    def address(self, value: str) -> None:
        self._server = (value, self._server[1])

    def init_keep_alive(self) -> None:
        self.logger.debug("Init keep alive")
        self._keep_alive = True
        self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())

    async def _keep_alive_loop(self) -> None:
        while True:
            self._sent_keep_alive = False
            try:
                await asyncio.sleep(self.keep_alive_timeout)
            except asyncio.CancelledError:
                return
            if not self._sent_keep_alive:
                self._send_keep_alive()

    def _send_keep_alive(self) -> None:
        logging.debug("Keep alive")
        self._transport.sendto(self._keep_alive_msg, self._server)
        self._sent_keep_alive = True

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        sock = transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # if not self._keep_alive:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.logger.debug("Command socket connected")
        self._transport = cast(asyncio.DatagramTransport, transport)
        self._connected.set_result(None)

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        msg = protocol.unpack(protocol.Buffer(data))
        if type(msg) in self._response_cb:
            self._response_cb[type(msg)](msg, addr)
        if self._response_type and isinstance(msg, self._response_type):
            self._response_type = None
            self._response.set_result(msg)
        if isinstance(msg, protocol.MoCapData):
            self._cb(msg)
            if self._keep_alive:
                pass
                # self._send_keep_alive()
                # self._transport.sendto(self._keep_alive_msg, addr)

    def error_received(self, exc: Any) -> None:
        self.logger.error(f'{exc}')

    def connection_lost(self, exc: Any) -> None:
        self.logger.warning("Command socket closed")
        self._done.set_result(None)

    def stop_keep_alive(self) -> None:
        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel()
            self._keep_alive = False

    def close(self) -> None:
        self.stop_keep_alive()

    async def send_request(
        self, data: bytes, timeout: float = 0.0
    ) -> protocol.Response | None:
        return await self.send(protocol.Request(data), protocol.Response, timeout)

    async def send(
        self, msg: protocol.Msg, response_type: Type[T], timeout: float = 0.0
    ) -> T | None:
        data = protocol.pack(msg)
        self._response: asyncio.Future[T] = asyncio.get_running_loop().create_future()
        self._response_type = response_type
        self._transport.sendto(data, self._server)
        if timeout > 0:
            try:
                return await asyncio.wait_for(self._response, timeout)
            except asyncio.exceptions.TimeoutError:
                self.logger.warning(f"Command request {msg} timed out after {timeout} s")
                return None
        else:
            return await self._response

    async def send_echo(
        self, stamp: int, timeout: float = 0.0
    ) -> protocol.EchoResponse | None:
        return await self.send(
            protocol.EchoRequest(stamp), protocol.EchoResponse, timeout
        )

    async def connect(self, timeout: float = 0.0) -> protocol.ServerInfo | None:
        return await self.send(
            protocol.ConnectRequest(), protocol.ServerInfo, timeout=timeout
        )

    async def get_description(
        self, timeout: float = 0.0
    ) -> protocol.MoCapDescription | None:
        return await self.send(
            protocol.ModelDefRequest(),
            protocol.MoCapDescription,
            timeout=timeout,
        )

    async def discover(
        self, broadcast_address: str, timeout: float = 5.0, number: int = 1
    ) -> dict[tuple[str, int], protocol.ServerInfo]:
        self.logger.info(f"Discovering servers (number={number})")
        self.logger.debug(f"Sending discovery message to {broadcast_address}:{self._server[1]}")
        data = protocol.pack(protocol.DiscoveryRequest())
        self._transport.sendto(data, (broadcast_address, self._server[1]))
        # self.logger.debug("Has sent discovery message")
        servers: dict[tuple[str, int], protocol.ServerInfo] = {}
        complete: asyncio.Future[None] = asyncio.get_running_loop().create_future()

        def cb(msg: protocol.ServerInfo, addr: tuple[str, int]) -> None:
            servers[addr] = msg
            self.logger.debug(f"Discovered server {addr[0]}:{addr[1]}: {msg}")
            if number > 0 and len(servers) >= number:
                complete.set_result(None)

        self._response_cb[protocol.ServerInfo] = cb

        try:
            await asyncio.wait_for(complete, timeout)
        except asyncio.exceptions.TimeoutError:
            self.logger.warning("Discovery timed out")

        del self._response_cb[protocol.ServerInfo]
        self.logger.info(f"Discovered {len(servers)} servers")
        return servers


class AsyncClient:
    """
    This class describes a Natnet client.

    Usage:

    1. Create the client

       >>> client = AsyncClient()

    2. Discover a server

       >>> servers = await client.discover(broadcast_address=255.255.255.255, timeout=1)

    3. and/or connect to a server directly

       >>> await client.connet(server_address=127.0.0.1)

    3. Read data

       >>> await client.get_data()

       or add a callback

       >>> client.data_callback = lambda time_ns, msg: print(time_ns, msg)

    4. and/or wait for some time or until disconnection

       >>> await client.wait(duration=60.0)

    5. close the connection

       >>> await client.unconnect()

    6. close the client

       >>> await client.close()

    """
    def __init__(
        self,
        address: str = "0.0.0.0",
        command_port: int = 1510,
        queue: int = 10,
        logger: logging.Logger = logging.getLogger(),
        now: clock.NanoSecondGetter = time.time_ns,
        sync: bool = True,
    ):
        """
        Construct an instance

        :param address: The IP4 address of the client.
                        Leave to ``"0.0.0.0"`` to bind to all interfaces.
        :param command_port: The port to send commands to.
        :param queue: length of the incoming mocap messages queue
        :param logger: the logger to use
        :param now: a function used to stamp incoming messages
        :param sync: whether to sync the client and server clocks upon connection
        """
        # The IP address of your local network interface
        self.client_address = address
        # NatNet Command channel
        self.command_port = command_port
        if queue >= 0:
            self._queue: DataQueue | None = asyncio.Queue(maxsize=queue)
        else:
            self._queue = None
        self._data_callback: DataCallback | None = None
        # self.done_callback: DoneCallback | None = None
        self._server_info: protocol.ServerInfo | None = None
        self._description: protocol.MoCapDescription | None = None
        self._rigid_body_names: dict[int, str] = {}
        self.logger = logger
        self.data_transport: asyncio.DatagramTransport | None = None
        self.cmd_transport: asyncio.DatagramTransport | None = None
        self.data_protocol: DataProtocol | None = None
        self.cmd_protocol: CommandProtocol | None = None
        self.clock: clock.SynchronizedClock | None = None
        self.data_has_unconnected: asyncio.Future[None] | None = None
        self.command_has_unconnected: asyncio.Future[None] | None = None
        self._now = now
        self._sync = sync

    @property
    def rigid_body_names(self) -> dict[int, str]:
        return self._rigid_body_names

    @property
    def data_callback(self) -> DataCallback | None:
        return self._data_callback

    @data_callback.setter
    def data_callback(self, value: DataCallback | None) -> None:
        self._data_callback = value

    @property
    def server_info(self) -> protocol.ServerInfo | None:
        """The connected server"""
        return self._server_info

    @server_info.setter
    def server_info(self, value: protocol.ServerInfo) -> None:
        self._server_info = value
        if value:
            version = value.nat_net_stream_version_server
            protocol.set_version(version.major, version.minor)

    @property
    def description(self) -> protocol.MoCapDescription | None:
        """The connected mocap description"""
        return self._description

    @description.setter
    def description(self, value: protocol.MoCapDescription | None) -> None:
        self._description = value
        if value:
            self._rigid_body_names = {rb.id: rb.name for rb in value.rigid_bodies}
        else:
            self._rigid_body_names = {}

    async def update_description(self, timeout: float = 0.0) -> None:
        """ Require a new description from the connected server

            Automatically called after connecting a server.
        """
        if self.cmd_protocol:
            self.description = await self.cmd_protocol.get_description(timeout)

    async def send_request(
        self, data: bytes, timeout: float = 0.0
    ) -> protocol.Response | None:
        if self.cmd_protocol:
            self.logger.debug(f"Sending request: {data.decode('ascii')}")
            return await self.cmd_protocol.send_request(data, timeout)
        return None

    async def set_property(
        self, name: bytes, value: Any, node: bytes = b"", timeout: float = 0.0
    ) -> bool:
        data = tokenize(b"SetProperty", node, name, str(value).encode("ascii"))
        response = await self.send_request(data, timeout=timeout)
        if response:
            r: int = struct.unpack("<i", response.data)[0]
            return r == 0
        return False

    async def get_property(
        self, name: bytes, kind: Type[T], node: bytes = b"", timeout: float = 0.0
    ) -> T | None:
        # TODO(Jerome): not sure it's should delete empty tokens.
        # They list this as an example: `"GetProperty,,MoodLiveColor"`
        # Maybe this is also valid for the other tokens
        data = tokenize(b"GetProperty", node, name)
        response = await self.send_request(data, timeout=timeout)
        if response:
            return kind(response.data)  # type: ignore
        return None

    async def set_framerate(self, rate: int, timeout: float = 0.0) -> bool:
        """
        Sets the framerate.

        :param      rate:     The desired framerate
        :param      timeout:  The timeout for the request

        :returns:   True if successful
        """
        return await self.set_property(b"Master Rate", rate, timeout=timeout)

    async def get_framerate(self) -> float | None:
        """
        Gets the framerate.

        :returns:  The framerate in Hz or None if the request was not successful
        """
        response = await self.send_request(b"FrameRate")
        if response:
            r: float = struct.unpack("<f", response.data)[0]
            return r
        return None

    async def enable_asset(self, name: bytes, timeout: float = 0.0) -> bool:
        """
        Enables the asset.

        :param      name:     The name of the asset
        :param      timeout:  The timeout for the request

        :returns:   True if successful
        """
        data = tokenize(b"EnableAsset", name)
        response = await self.send_request(data, timeout=timeout)
        if response:
            return True
        return False

    async def disable_asset(self, name: bytes, timeout: float = 0.0) -> bool:
        """
        Disables the asset.

        :param      name:     The name of the asset
        :param      timeout:  The timeout for the request

        :returns:   True if successful
        """
        data = tokenize(b"DisableAsset", name)
        response = await self.send_request(data, timeout=timeout)
        if response:
            return True
        return False

    async def clear_subscribtions(self, timeout: float = 0.0) -> bool:
        """
        Unsubscribe (requires NatNet >= 4)

        :param      timeout:  The request timeout

        :returns:   True if successful
        """
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        r = (
            await self.send_request(b"SubscribeToData", timeout=timeout)
            is not None
        )
        if r:
            return (
                await self.send_request(b"SubscribeByID", timeout=timeout)
                is not None
            )
        return r

    async def subscribe(
        self,
        kind: bytes = b"RigidBody",
        name: bytes = b"",
        id: int = 0,
        timeout: float = 0.0,
    ) -> bool:
        """
        Subscribe (requires NatNet >= 4)

        :param      kind:  The type of the asset
        :param      name:  The name of the asset
        :param      id:   The id of the asset
        :param      timeout:  The request timeout

        :returns:   True if successful
        """
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        if name:
            data = tokenize(b"SubscribeToData", kind, name)
        else:
            data = tokenize(b"SubscribeByID", kind, str(id).encode("ascii"))
        response = await self.send_request(data, timeout=timeout)
        return response is not None

    async def subscribe_all(self, timeout: float = 0.0) -> bool:
        """
        Subscribe (requires NatNet >= 4) to all rigid bodies

        :param      timeout:  The request timeout

        :returns:   True if successful
        """
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        data = b"SubscribeToData,RigidBody,all"
        response = await self.send_request(data, timeout=timeout)
        return response is not None

    async def unsubscribe(
        self, name: bytes = b"", id: int = 0, timeout: float = 0.0
    ) -> bool:
        """
        Unsubscribe (requires NatNet >= 4) from a rigid body updates

        :param      name:  The name of the asset
        :param      id:   The id of the asset
        :param      timeout:  The request timeout

        :returns:   True if successful
        """
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        if name:
            data = tokenize(b"SubscribeToData,RigidBody", name, b"None")
        else:
            data = tokenize(
                b"SubscribeByID,RigidBody", str(id).encode("ascii"), b"None"
            )
        response = await self.send_request(data, timeout=timeout)
        return response is not None

    @property
    def use_multicast(self) -> bool:
        """
        Whether the server is using multicasting to stream data

        :returns:   True if multicasting
        """
        if not self.server_info or not self.server_info.connection_info:
            return False
        return self.server_info.connection_info.multicast

    @property
    def multicast_address(self) -> str:
        """
        The server IP4 multicast address

        :returns:   An IP4 address
        """
        if not self.server_info or not self.server_info.connection_info:
            return ''
        return self.server_info.connection_info.multicast_address

    @property
    def data_port(self) -> int:
        """
        The configured data port

        :returns:   The server actual port or the default port
        """
        if not self.server_info or not self.server_info.connection_info:
            return 0
        return self.server_info.connection_info.data_port

    @property
    def can_change_bitstream_version(self) -> bool:
        """
        Whether the client may ask to change natnet protocol version.

        :returns:   True if able to change bitstream version, False otherwise.
        """
        major, _ = protocol.get_version()
        return major >= 4 and not self.use_multicast

    @property
    def can_subscribe(self) -> bool:
        """
        Determines ability to subscribe (which requires NatNet >= 4).

        :returns:   True if able to subscribe, False otherwise.
        """
        major, _ = protocol.get_version()
        return major >= 4 and not self.use_multicast

    async def set_version(self, major: int, minor: int) -> bool:
        """
        Sets the protocol version.

        :param      major:  The major version number
        :param      minor:  The minor version number

        :returns:   True if successful
        """
        if not self.can_change_bitstream_version:
            logging.warning("Cannot set bitstream version")
            return False
        c_major, c_minor = protocol.get_version()
        if c_major != major or c_minor != minor:
            logging.debug("Trying to set bitstream version to {major},{minor}")
            data = b"Bitstream,%1.1d.%1.1d" % (major, minor)
            response = await self.send_request(data)
            if not response:
                logging.warning("Failed to set bitstream version")
                return False
            logging.debug("Set bitstream version")
            protocol.set_version(major, minor)
        return True

    def _callback(self, msg: protocol.MoCapData) -> None:
        data = (self._now(), msg)
        if self._queue:
            if self._queue.full():
                self._queue.get_nowait()
            self._queue.put_nowait(data)
        if self.data_callback:
            self.data_callback(*data)

    async def discover(
        self, broadcast_address: str, number: int = -1, timeout: float = 5.0
    ) -> dict[tuple[str, int], protocol.ServerInfo]:
        """
        Discover Motive Natnet servers

        :param broadcast_address: The IPv4 broadcast address to announce this client
        :param timeout:           The maximal time to wait to discover enough services
        :param number:            The maximal number of services to discover.
                                  It will return after the first ``maximal_number``
                                  servers are discovered.

        :returns:  A dictionary of server information keyed by server address.
        """
        await self.init()
        if self.cmd_protocol:
            return await self.cmd_protocol.discover(
                broadcast_address=broadcast_address, timeout=timeout, number=number)
        return {}

    async def init(self) -> None:
        if self.cmd_transport is not None:
            return
        loop = asyncio.get_running_loop()

        self.command_has_connected = loop.create_future()
        self.command_has_unconnected = loop.create_future()
        self.command_has_unconnected.add_done_callback(self._has_unconnected_command)
        self.logger.info(f"Opening command socket on {self.client_address}")
        self.cmd_transport, self.cmd_protocol = await loop.create_datagram_endpoint(
            lambda: CommandProtocol(
                '',
                self.command_port,
                self._callback,
                cast(asyncio.Future[None], self.command_has_connected),
                cast(asyncio.Future[None], self.command_has_unconnected),
                self.logger,
            ),
            family=socket.AF_INET,
            # local_addr=('', 0))
            local_addr=(self.client_address, 0),
        )
        await self.command_has_connected

    @property
    def server_address(self) -> tuple[str, int] | None:
        """The IP4 address and port of the connected server

        :returns: (IP4 address, port) or None if not connected

        """
        if self.connected and self.cmd_protocol:
            return self.cmd_protocol._server
        return None

    # Create a data socket to attach to the NatNet stream
    async def connect(
        self,
        discovery_address: str = '',
        server_address: str = '127.0.0.1',
        timeout: float = 5.0,
        start_listening_for_data: bool = True,
    ) -> bool:
        """
            Connect to a server. If the broadcast address is configured,
            it will first try to discover reachable NatNet servers in the network.

            :param discovery_address: The IP4 broadcast address where servers announce themselves.
                                      If not set, it will not perform auto-discovery.
            :param server_address: The IP4 address of the NatNet server.
                                   Only used if auto-discovery is not performed.
            :param timeout: the timeout for the server to be discovered and
                            for it to accept connection.
            :param start_listening_for_data: whether to start listening for incoming mocap data.
                                             If not set, we can trigger this later using
                                             :py:meth:`start_listening_for_data`.


            Once a server connects, the client automatically requires an updated description,
            and updates :py:attr:`rigid_bodies_names`.


            :returns:   True if successful
        """
        if self.connected:
            self.logger.warning(
                "Please disconnect from the current server before "
                "try to connect to a new server")
            return False
        await self.init()
        if not self.cmd_protocol:
            self.logger.warning("Client not initialized")
            return False
        server = (server_address, self.command_port)
        if discovery_address:
            servers = await self.discover(
                broadcast_address=discovery_address, timeout=timeout, number=1)
            if servers:
                server, self.server_info = next(iter(servers.items()))
                self.cmd_protocol._server = server
                self.logger.debug(f"Received server info {self.server_info}")
                self.logger.info(f"Connected to server {server[0]}:{server[1]}")
            else:
                return False
        else:
            self.logger.info(f"Connecting to {server_address} ...")
            # TODO(Jerome): do I really need to call it now?
            self.server_info = await self.cmd_protocol.connect(timeout)
            if not self.server_info:
                self.logger.warning("Failed connecting.")
                return False
            else:
                self.logger.debug(f"Received server info {self.server_info}")
            self.logger.info(f"Connected to server {server[0]}:{server[1]}")
        await self.update_description(timeout)
        if not self.description:
            return False
        self.logger.debug(f"Received server description {self.description}")
        # self.logger.info(
        #     f"Got description for rigid bodies: {', '.join(self.rigid_body_names.values())}"
        # )
        if self._sync:
            self.clock = clock.SynchronizedClock(
                self.cmd_protocol,
                server_info=self.server_info,
                logger=self.logger,
                now=self._now,
            )
            await self.clock.init()
        if start_listening_for_data:
            return await self.start_listening_for_data()
        return True

    async def start_listening_for_data(self, timeout: float = 5.0) -> bool:
        """
        Starts a listening for data.

        :param      timeout:  The request timeout

        :returns:   True if successful
        """
        if not self.cmd_protocol or not self.server_info:
            self.logger.warning("Trying to start listening for data before connecting")
            return False
        loop = asyncio.get_running_loop()
        membership = socket.inet_aton(self.multicast_address) + socket.inet_aton(
            self.client_address
        )
        self.data_has_unconnected = loop.create_future()
        self.data_has_unconnected.add_done_callback(self._has_unconnected_data)
        self.logger.info(
            f"Opening data {'multicast' if self.use_multicast else 'unicast'}"
            f" socket on {self.client_address}:{self.data_port}"
        )
        if self.use_multicast:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
                sock.bind(("", self.data_port))
            except (
                OSError,
                socket.error,
                socket.herror,
                socket.gaierror,
                socket.timeout,
            ) as msg:
                self.logger.error(str(msg))
                self.data_has_unconnected.set_result(None)
                return False
            (
                self.data_transport,
                self.data_protocol,
            ) = await loop.create_datagram_endpoint(
                lambda: DataProtocol(
                    membership,
                    self._callback,
                    cast(asyncio.Future[None], self.data_has_unconnected),
                    self.logger,
                ),
                sock=sock,
            )
        else:
            (
                self.data_transport,
                self.data_protocol,
            ) = await loop.create_datagram_endpoint(
                lambda: DataProtocol(
                    membership,
                    self._callback,
                    cast(asyncio.Future[None], self.data_has_unconnected),
                    self.logger,
                ),
                # local_addr=(self.client_address, 0),
                local_addr=(self.client_address, self.data_port),
                family=socket.AF_INET,
                proto=socket.IPPROTO_UDP,
            )
            # TODO(Jerome): do I need to send it twice?
            await self.cmd_protocol.connect(timeout)
            self.cmd_protocol.init_keep_alive()
        return True

    def _unconnect_server(self) -> None:
        if self.data_transport:
            if not self.data_transport.is_closing():
                self.data_transport.close()
            self.data_transport = None
        if self.cmd_protocol:
            self.cmd_protocol.stop_keep_alive()
        self.data_protocol = None
        if self.clock:
            self.clock.stop()
            self.clock = None
        self.server_info = None
        self.description = None
        self._rigid_body_names = {}

    def _unconnect_client(self) -> None:
        self._unconnect_server()
        if self.cmd_protocol:
            self.cmd_protocol.close()
            self.cmd_protocol = None
        if self.cmd_transport:
            if not self.cmd_transport.is_closing():
                self.cmd_transport.close()
            self.cmd_transport = None

    def _has_unconnected_data(self, future: asyncio.Future[None]) -> None:
        self._unconnect_server()

    def _has_unconnected_command(self, future: asyncio.Future[None]) -> None:
        self._unconnect_client()

    async def unconnect(self) -> None:
        """
        Unconnect the currently connected server

        :returns:   True if successful
        """
        logging.info("Unconnecting server ...")
        self._unconnect_server()
        if self.data_has_unconnected:
            await asyncio.wait([self.data_has_unconnected])
        self.logger.info("Unconnected")

    async def close(self) -> None:
        """
        Closes the client connections.
        """
        logging.info("Closing client ...")
        self._unconnect_client()
        if self.command_has_unconnected:
            await asyncio.wait([self.command_has_unconnected])
        self.logger.info("Closed")

    @property
    def connected(self) -> bool:
        """
        Whether a NatNet server is connected.

        :returns:   True if connected else False
        """
        return self.server_info is not None

    async def wait_until_lost_connection(self) -> bool:
        try:
            await asyncio.wait(
                filter(None, [self.data_has_unconnected, self.command_has_unconnected]),
                return_when=asyncio.FIRST_COMPLETED,
            )
            logging.warning("Lost connection")
            return True
        except asyncio.exceptions.CancelledError:
            return False

    async def get_data(
        self, timeout: float = 0.0, last: bool = False
    ) -> tuple[int, protocol.MoCapData] | None:
        """
        Gets mocap data.

        :param      timeout:  The timeout
        :param      last:     whether to ignore the queue and fetch only the last data

        :returns:   The (receiving stamp in ns, data) or None if not available
        """
        if self._queue:
            if not self._queue.empty() and last:
                while not self._queue.empty():
                    value = self._queue.get_nowait()
                return value
            if timeout > 0:
                try:
                    return await asyncio.wait_for(self._queue.get(), timeout)
                except asyncio.exceptions.TimeoutError:
                    self.logger.warning("Timed out")
                    return None
            return await self._queue.get()
        self.logger.error("No queue")
        return None

    async def wait(self, duration: float) -> bool:
        """
        Wait a given duration or until the client has disconnected.

        :param      duration:  The duration to wait for

        :returns:   True if still connected
        """
        if duration > 0:
            try:
                r = await asyncio.wait_for(self.wait_until_lost_connection(), duration)
                return not r
            except TimeoutError:
                return True
        await self.wait_until_lost_connection()
        return False

    def server_ticks_to_client_ns_time(self, ticks: int) -> int:
        """
        Convert a server ticks to a time synchronized with the client clock

        :param      ticks:  The ticks

        :returns:   The time as nanoseconds since epoch
        """
        if self.clock:
            return self.clock.server_ticks_to_client_time(ticks)
        return 0
