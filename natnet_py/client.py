import socket
import logging
import asyncio
import struct
import time

from . import protocol
from . import clock

from typing import Any, Callable, Optional, Tuple, Dict, TypeVar, Type, cast

T = TypeVar("T")
DataCallback = Callable[[protocol.MoCapData], None]
DoneCallback = Callable[[], None]
DataQueue = asyncio.Queue[protocol.MoCapData]
ResponseCallback = Callable[[Any, Tuple[str, int]], None]


def tokenize(*tokens: bytes) -> bytes:
    return b",".join(filter(None, tokens))
    # return b",".join(tokens)


class DataProtocol(asyncio.Protocol):
    def __init__(
        self,
        membership: bytes,
        cb: DataCallback,
        done: asyncio.Future[None],
        logger: logging.Logger,
    ):
        self._membership = membership
        self._done = done
        self._cb = cb
        self.logger = logger
        self.version = (3, 1)
        self.logger.debug("Data socket initialized")

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        # sock = transport.get_extra_info("socket")
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
        #                 self._membership)
        self.logger.debug("Data socket connected")

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        # print('datagram_received', data, addr)
        msg = protocol.unpack(protocol.Buffer(data), *self.version)
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
        server: Tuple[str, int],
        cb: DataCallback,
        done: asyncio.Future[None],
        logger: logging.Logger,
    ):
        self._server = server
        self._response_type: Any = None
        self._response_cb: Dict[Any, ResponseCallback] = {}
        self._keep_alive_task: Optional[asyncio.Task[None]] = None
        self._keep_alive_msg = protocol.request(protocol.NAT.KEEPALIVE)
        self._cb = cb
        self._done = done
        self._keep_alive = False
        self.version = (3, 1)
        self.keep_alive_timeout = 5.0
        self.logger = logger
        self.logger.debug("Command socket initialized")

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

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        msg = protocol.unpack(protocol.Buffer(data), *self.version)
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

    def close(self) -> None:
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            self._keep_alive_task = None
            self._keep_alive = False

    async def send_request(
        self, data: bytes, timeout: float = 0.0
    ) -> Optional[protocol.Response]:
        self.logger.debug(f"{data}")
        return await self.send(
            protocol.request(protocol.NAT.REQUEST, data), protocol.Response, timeout
        )

    async def send(
        self, data: bytes, response_type: Type[T], timeout: float = 0.0
    ) -> Optional[T]:
        self._response: asyncio.Future[T] = asyncio.get_running_loop().create_future()
        self._response_type = response_type
        self._transport.sendto(data, self._server)
        if timeout > 0:
            try:
                return await asyncio.wait_for(self._response, timeout)
            except asyncio.exceptions.TimeoutError:
                self.logger.warning("Command socket request timed out")
                return None
        else:
            return await self._response

    async def send_echo(
        self, stamp: int, timeout: float = 0.0
    ) -> Optional[protocol.EchoResponse]:
        return await self.send(
            protocol.echo_request(stamp), protocol.EchoResponse, timeout
        )

    async def connect(self, timeout: float = 0.0) -> Optional[protocol.ServerInfo]:
        return await self.send(
            protocol.connect_request(), protocol.ServerInfo, timeout=timeout
        )

    async def get_description(
        self, timeout: float = 0.0
    ) -> Optional[protocol.DataDescriptions]:
        return await self.send(
            protocol.request(protocol.NAT.REQUEST_MODELDEF),
            protocol.DataDescriptions,
            timeout=timeout,
        )

    async def discover(
        self, broadcast_address: str, timeout: float = 5.0, number: int = 1
    ) -> Dict[Tuple[str, int], protocol.ServerInfo]:
        self._transport.sendto(
            protocol.discovery_request(), (broadcast_address, self._server[1])
        )
        servers: Dict[Tuple[str, int], protocol.ServerInfo] = {}
        complete: asyncio.Future[None] = asyncio.get_running_loop().create_future()

        def cb(msg: protocol.ServerInfo, addr: Tuple[str, int]) -> None:
            servers[addr] = msg
            if number > 0 and len(servers) >= number:
                complete.set_result(None)

        self._response_cb[protocol.ServerInfo] = cb

        try:
            await asyncio.wait_for(complete, timeout)
        except asyncio.exceptions.TimeoutError:
            self.logger.warning("Discovery timed out")

        del self._response_cb[protocol.ServerInfo]
        return servers


class NatNetClient:
    def __init__(
        self,
        server_address: str = "127.0.0.1",
        client_address: str = "127.0.0.1",
        multicast_address: str = "239.255.42.99",
        broadcast_address: str = "",
        use_multicast: bool = True,
        command_port: int = 1510,
        data_port: int = 1511,
        queue: int = 10,
        logger: logging.Logger = logging.getLogger(),
        now: Callable[[], int] = time.time_ns,
        sync: bool = True,
    ):
        # The IP address of the NatNet server.
        self.server_address = server_address
        # The IP address of your local network interface
        self.client_address = client_address
        # The multicast address listed in Motive's streaming settings.
        self._multicast_address = multicast_address
        self.broadcast_address = broadcast_address
        # NatNet Command channel
        self.command_port = command_port
        # NatNet Data channel
        self._data_port = data_port
        self._use_multicast = use_multicast
        if queue >= 0:
            self._queue: Optional[DataQueue] = asyncio.Queue(maxsize=queue)
        else:
            self._queue = None
        self.data_callback: Optional[DataCallback] = None
        self.done_callback: Optional[DoneCallback] = None
        self.server_info: Optional[protocol.ServerInfo] = None
        self.description: Optional[protocol.DataDescriptions] = None
        self.rigid_body_names: Dict[int, str] = {}
        self.logger = logger
        self.data_transport: Optional[asyncio.DatagramTransport] = None
        self.cmd_transport: Optional[asyncio.DatagramTransport] = None
        self.data_protocol: Optional[DataProtocol] = None
        self.cmd_protocol: Optional[CommandProtocol] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.clock: Optional[clock.SynchronizedClock] = None
        self.data_has_unconnected: Optional[asyncio.Future[None]] = None
        self.command_has_unconnected: Optional[asyncio.Future[None]] = None
        self._now = now
        self._sync = sync

    async def send_request_async(
        self, data: bytes, timeout: float = 0.0
    ) -> Optional[protocol.Response]:
        if self.cmd_protocol:
            self.logger.debug(f"Sending request: {data.decode('ascii')}")
            return await self.cmd_protocol.send_request(data, timeout)
        return None

    def send_request(
        self, data: bytes, timeout: float = 0.0
    ) -> Optional[protocol.Response]:
        if self._loop:
            return self._loop.run_until_complete(self.send_request_async(data, timeout))
        return None

    async def set_property_async(
        self, name: bytes, value: Any, node: bytes = b"", timeout: float = 0.0
    ) -> bool:
        data = tokenize(b"SetProperty", node, name, str(value).encode("ascii"))
        response = await self.send_request_async(data, timeout=timeout)
        if response:
            r: int = struct.unpack("<i", response.data)[0]
            return r == 0
        return False

    async def get_property_async(
        self, name: bytes, kind: Type[T], node: bytes = b"", timeout: float = 0.0
    ) -> Optional[T]:
        # TODO(Jerome): not sure it's should delete empty tokens.
        # They list this as an example: `"GetProperty,,MoodLiveColor"`
        # Maybe this is also valid for the other tokens
        data = tokenize(b"GetProperty", node, name)
        response = await self.send_request_async(data, timeout=timeout)
        if response:
            return kind(response.data)  # type: ignore
        return None

    async def set_framerate_async(self, rate: int, timeout: float = 0.0) -> bool:
        return await self.set_property_async(b"Master Rate", rate, timeout=timeout)

    async def get_framerate_async(self) -> Optional[float]:
        response = await self.send_request_async(b"FrameRate")
        if response:
            r: float = struct.unpack("<f", response.data)[0]
            return r
        return None

    async def enable_asset_async(self, name: bytes, timeout: float = 0.0) -> bool:
        data = tokenize(b"EnableAsset", name)
        response = await self.send_request_async(data, timeout=timeout)
        if response:
            return True
        return False

    async def disable_asset_async(self, name: bytes, timeout: float = 0.0) -> bool:
        data = tokenize(b"DisableAsset", name)
        response = await self.send_request_async(data, timeout=timeout)
        if response:
            return True
        return False

    async def clear_subscribtions_async(self, timeout: float = 0.0) -> bool:
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        r = (
            await self.send_request_async(b"SubscribeToData", timeout=timeout)
            is not None
        )
        if r:
            return (
                await self.send_request_async(b"SubscribeByID", timeout=timeout)
                is not None
            )
        return r

    async def subscribe_async(
        self,
        kind: bytes = b"RigidBody",
        name: bytes = b"",
        id: int = 0,
        timeout: float = 0.0,
    ) -> bool:
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        if name:
            data = tokenize(b"SubscribeToData", kind, name)
        else:
            data = tokenize(b"SubscribeByID", kind, str(id).encode("ascii"))
        response = await self.send_request_async(data, timeout=timeout)
        return response is not None

    async def subscribe_all_async(self, timeout: float = 0.0) -> bool:
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        data = b"SubscribeToData,RigidBody,all"
        response = await self.send_request_async(data, timeout=timeout)
        return response is not None

    async def unsubscribe_async(
        self, name: bytes = b"", id: int = 0, timeout: float = 0.0
    ) -> bool:
        if self.can_subscribe:
            self.logger.warning("Subscription commands not available")
            return False
        if name:
            data = tokenize(b"SubscribeToData,RigidBody", name, b"None")
        else:
            data = tokenize(
                b"SubscribeByID,RigidBody", str(id).encode("ascii"), b"None"
            )
        response = await self.send_request_async(data, timeout=timeout)
        return response is not None

    @property
    def use_multicast(self) -> bool:
        if not self.server_info or not self.server_info.connection_info:
            return self._use_multicast
        return self.server_info.connection_info.multicast

    @property
    def multicast_address(self) -> str:
        if not self.server_info or not self.server_info.connection_info:
            return self._multicast_address
        return self.server_info.connection_info.multicast_address

    @property
    def data_port(self) -> int:
        if not self.server_info or not self.server_info.connection_info:
            return self._data_port
        return self.server_info.connection_info.data_port

    @property
    def can_change_bitstream_version(self) -> bool:
        return self.version[0] >= 4 and not self.use_multicast

    @property
    def can_subscribe(self) -> bool:
        return self.version[0] >= 4 and not self.use_multicast

    async def set_version_async(self, major: int, minor: int) -> bool:
        if not self.can_change_bitstream_version:
            logging.warning("Cannot set bitstream version")
            return False
        c_major, c_minor = self.version
        if c_major != major or c_minor != minor:
            logging.debug("Trying to set bitstream version to {major},{minor}")
            data = b"Bitstream,%1.1d.%1.1d" % (major, minor)
            response = await self.send_request_async(data)
            if not response:
                logging.warning("Failed to set bitstream version")
                return False
            logging.debug("Set bitstream version")
            self.version = (major, minor)
        return True

    def _data_callback(self, msg: protocol.MoCapData) -> None:
        if self._queue:
            if self._queue.full():
                self._queue.get_nowait()
            self._queue.put_nowait(msg)
        if self.data_callback:
            self.data_callback(msg)

    @property
    def version(self) -> Tuple[int, int]:
        if not self.server_info:
            return (0, 0)
        vs = self.server_info.nat_net_stream_version_server
        return vs[:2]

    @version.setter
    def version(self, value: Tuple[int, int]) -> None:
        if not self.server_info:
            return
        if self.cmd_protocol:
            self.cmd_protocol.version = value
        if self.data_protocol:
            self.data_protocol.version = value
        vs = self.server_info.nat_net_stream_version_server
        self.server_info.nat_net_stream_version_server = (*value, *vs[2:])

    # Create a data socket to attach to the NatNet stream
    async def connect_async(
        self,
        timeout: float = 5.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        start_listening_for_data: bool = True,
    ) -> bool:
        if not loop:
            loop = asyncio.get_running_loop()

        self.command_has_unconnected = loop.create_future()
        self.command_has_unconnected.add_done_callback(self._has_unconnected)

        server = (self.server_address, self.command_port)
        self.logger.debug(f"Creating command socket {server}")
        self.cmd_transport, self.cmd_protocol = await loop.create_datagram_endpoint(
            lambda: CommandProtocol(
                server,
                self._data_callback,
                cast(asyncio.Future[None], self.command_has_unconnected),
                self.logger,
            ),
            # local_addr=('', 0))
            local_addr=(self.client_address, 0),
        )

        if self.broadcast_address:
            self.logger.debug(f"Discovering servers on {self.broadcast_address} ...")
            servers = await self.cmd_protocol.discover(
                broadcast_address=self.broadcast_address, timeout=timeout, number=1
            )
            self.logger.debug(f"Discovered servers: {servers}")
            if servers:
                self.cmd_protocol._server, self.server_info = next(
                    iter(servers.items())
                )
                # await self.cmd_protocol.connect(timeout)
            else:
                return False
        else:
            self.logger.debug(f"Connecting to server at {self.server_address} ...")
            self.server_info = await self.cmd_protocol.connect(timeout)
            if not self.server_info:
                self.logger.warning("Failed connecting.")
                return False
            self.logger.debug(f"Connected: {self.server_info}")
        self.cmd_protocol.version = self.server_info.nat_net_stream_version_server[:2]
        self.description = await self.cmd_protocol.get_description(timeout)
        if not self.description:
            return False
        self.rigid_body_names = {
            rb.new_id: rb.name for rb in self.description.rigid_bodies
        }
        self.logger.info(
            f"Got description for rigid bodies: {', '.join(self.rigid_body_names.values())}"
        )

        if self._sync:
            self.clock = clock.SynchronizedClock(
                self.cmd_protocol,
                server_info=self.server_info,
                logger=self.logger,
                now=self._now,
            )
            self.clock.init()

        self.logger.info(f"NatNet client connected: {self.server_info}")
        if start_listening_for_data:
            return await self.start_listening_for_data_async(loop=loop)
        return True

    def connect(
        self, timeout: float = 5.0, start_listening_for_data: bool = True
    ) -> bool:
        if self._loop:
            return False
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(
            self.connect_async(
                timeout,
                loop=self._loop,
                start_listening_for_data=start_listening_for_data,
            )
        )

    async def start_listening_for_data_async(
        self, timeout: float = 5.0, loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> bool:
        if not self.cmd_protocol or not self.server_info:
            self.logger.warning("Trying to start listening for data before connecting")
            return False
        if not loop:
            loop = asyncio.get_running_loop()
        membership = socket.inet_aton(self.multicast_address) + socket.inet_aton(
            self.client_address
        )
        self.data_has_unconnected = loop.create_future()
        self.data_has_unconnected.add_done_callback(self._has_unconnected)
        self.logger.info(
            f"Creating data {'multicast' if self.use_multicast else 'unicast'}"
            f" socket on port {self.data_port}"
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
                    self._data_callback,
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
                    self._data_callback,
                    cast(asyncio.Future[None], self.data_has_unconnected),
                    self.logger,
                ),
                local_addr=(self.client_address, 0),
                family=socket.AF_INET,
                proto=socket.IPPROTO_UDP,
            )
            await self.cmd_protocol.connect(timeout)
            self.cmd_protocol.init_keep_alive()
        self.data_protocol.version = self.server_info.nat_net_stream_version_server[:2]
        return True

    def start_listening_for_data(self) -> bool:
        if self._loop:
            return False
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(
            self.start_listening_for_data_async(loop=self._loop)
        )

    def _unconnect(self) -> None:
        if self.data_transport:
            if not self.data_transport.is_closing():
                self.data_transport.close()
            self.data_transport = None
        self.data_protocol = None
        if self.cmd_protocol:
            self.cmd_protocol.close()
            self.cmd_protocol = None
        if self.cmd_transport:
            if not self.cmd_transport.is_closing():
                self.cmd_transport.close()
            self.cmd_transport = None
        if self.clock:
            self.clock.stop()
            self.clock = None
        self.server_info = None
        self.description = None
        self.rigid_body_names = {}

    def _has_unconnected(self, future: asyncio.Future[None]) -> None:
        self._unconnect()

    async def unconnect_async(self) -> None:
        self._unconnect()
        await asyncio.wait(
            filter(None, [self.data_has_unconnected, self.command_has_unconnected])
        )

    def unconnect(self) -> None:
        if self._loop:
            self._loop.run_until_complete(self.unconnect_async())
            self._loop.stop()
            self._loop.close()
            self._loop = None

    @property
    def connected(self) -> bool:
        return self.server_info is not None

    async def wait_until_lost_connection(self) -> None:
        try:
            await asyncio.wait(
                filter(None, [self.data_has_unconnected, self.command_has_unconnected]),
                return_when=asyncio.FIRST_COMPLETED,
            )
        except asyncio.exceptions.CancelledError:
            pass

    async def get_data_async(
        self, timeout: float = 0.0, last: bool = False
    ) -> Optional[protocol.MoCapData]:
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

    def get_data(
        self, timeout: float = 0.0, last: bool = False
    ) -> Optional[protocol.MoCapData]:
        if self._loop:
            return self._loop.run_until_complete(
                self.get_data_async(timeout, last=last)
            )
        return None

    async def run_async(self, duration: float) -> bool:
        if duration > 0:
            try:
                await asyncio.wait_for(self.wait_until_lost_connection(), duration)
                return False
            except TimeoutError:
                return True
        await self.wait_until_lost_connection()
        return False

    def run(self, duration: float) -> bool:
        if self._loop:
            return self._loop.run_until_complete(self.run_async(duration))
        return False
