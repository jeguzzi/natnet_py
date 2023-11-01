import socket
import logging
import asyncio

from . import protocol

from typing import Any, Callable, Optional, Tuple, Dict, TypeVar, Type, cast

DataCallback = Callable[[protocol.MoCapData], None]
DoneCallback = Callable[[], None]
T = TypeVar("T")


class DataProtocol(asyncio.Protocol):
    def __init__(self, membership: bytes, cb: DataCallback,
                 done: asyncio.Future[None], logger: logging.Logger):
        self._membership = membership
        self._done = done
        self._cb = cb
        self.logger = logger
        self.logger.debug('Data socket initialized')

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        # sock = transport.get_extra_info("socket")
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
        #                 self._membership)
        self.logger.debug('Data socket connected')

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        msg = protocol.unpack(protocol.Buffer(data), 3, 1)
        if isinstance(msg, protocol.MoCapData):
            self._cb(msg)

    def error_received(self, exc: Any) -> None:
        self.logger.error(exc)

    def connection_lost(self, exc: Any) -> None:
        self.logger.warning("Data socket closed")
        self._done.set_result(None)


class CommandProtocol(asyncio.Protocol):
    def __init__(self, server: Tuple[str, int], keep_alive: bool,
                 cb: DataCallback, done: asyncio.Future[None],
                 logger: logging.Logger):
        self._server = server
        self._response_type: Any = None
        self._keep_alive_task: Optional[asyncio.Task[None]] = None
        self._keep_alive_msg = protocol.request(protocol.NAT.KEEPALIVE)
        self._cb = cb
        self._done = done
        self._keep_alive = keep_alive
        self.version = (3, 1)
        self.logger = logger
        self.logger.debug('Command socket initialized')

    def init_keep_alive(self) -> None:
        if self._keep_alive:
            self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())

    async def _keep_alive_loop(self) -> None:
        while True:
            self._sent_keep_alive = False
            try:
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                return
            if not self._sent_keep_alive:
                self._send_keep_alive()

    def _send_keep_alive(self) -> None:
        self._transport.sendto(self._keep_alive_msg, self._server)
        self._sent_keep_alive = True

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        sock = transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not self._keep_alive:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.logger.debug('Command socket connected')
        self._transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        msg = protocol.unpack(protocol.Buffer(data), *self.version)
        if self._response_type and isinstance(msg, self._response_type):
            self._response_type = None
            self._response.set_result(msg)
        if isinstance(msg, protocol.MoCapData):
            self._cb(msg)
            if self._keep_alive:
                self._send_keep_alive()
                # self._transport.sendto(self._keep_alive_msg, addr)

    def error_received(self, exc: Any) -> None:
        self.logger.error(exc)

    def connection_lost(self, exc: Any) -> None:
        self.logger.warning("Command socket closed")
        self._done.set_result(None)

    def close(self) -> None:
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            self._keep_alive_task = None

    async def send(self, data: bytes, response_type: Type[T], timeout: float = 0.0) -> Optional[T]:
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

    async def connect(self, timeout: float = 0.0) -> Optional[protocol.ServerInfo]:
        return await self.send(
            protocol.request(protocol.NAT.CONNECT), protocol.ServerInfo,
            timeout=timeout)

    async def get_description(self, timeout: float = 0.0) -> Optional[protocol.DataDescriptions]:
        return await self.send(
            protocol.request(protocol.NAT.REQUEST_MODELDEF), protocol.DataDescriptions,
            timeout=timeout)


class NatNetClient:
    def __init__(self, server_address: str = "127.0.0.1",
                 client_address: str = "127.0.0.1",
                 multicast_address: str = "239.255.42.99",
                 use_multicast: bool = True, command_port: int = 1510,
                 data_port: int = 1511, queue: int = 10,
                 logger: logging.Logger = logging.getLogger()):
        # The IP address of the NatNet server.
        self.server_address = server_address
        # The IP address of your local network interface
        self.client_address = client_address
        # The multicast address listed in Motive's streaming settings.
        self.multicast_address = multicast_address
        # NatNet Command channel
        self.command_port = command_port
        # NatNet Data channel
        self.data_port = data_port
        self.use_multicast = use_multicast
        if queue >= 0:
            self._queue: Optional[asyncio.Queue[protocol.MoCapData]] = asyncio.Queue(maxsize=queue)
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

    @property
    def can_change_bitstream_version(self) -> bool:
        if not self.server_info:
            return False
        return (self.server_info.nat_net_stream_version_server[0] >= 4
                and not self.use_multicast)

    def _data_callback(self, msg: protocol.MoCapData) -> None:
        if self._queue:
            if self._queue.full():
                self._queue.get_nowait()
            self._queue.put_nowait(msg)
        if self.data_callback:
            self.data_callback(msg)

    # Create a data socket to attach to the NatNet stream
    async def connect_async(self, timeout: float = 5.0, loop: Optional[asyncio.AbstractEventLoop] = None) -> bool:

        if not loop:
            loop = asyncio.get_running_loop()
        membership = (socket.inet_aton(self.multicast_address) +
                      socket.inet_aton(self.client_address))

        self.data_has_unconnected = loop.create_future()
        self.command_has_unconnected = loop.create_future()
        self.data_has_unconnected.add_done_callback(self._has_unconnected)
        self.command_has_unconnected.add_done_callback(self._has_unconnected)

        if self.use_multicast:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
                sock.bind(("", self.data_port) )
            except (OSError, socket.error, socket.herror, socket.gaierror, socket.timeout) as msg:
                self.logger.error(str(msg))
                self.data_has_unconnected.set_result(None)
                self.command_has_unconnected.set_result(None)
                return False
            self.data_transport, self.data_protocol= await loop.create_datagram_endpoint(
                lambda: DataProtocol(membership, self._data_callback,
                                     self.data_has_unconnected, self.logger), sock=sock
            )
        else:
            self.data_transport, self.data_protocol = await loop.create_datagram_endpoint(
                lambda: DataProtocol(membership, self._data_callback,
                                     self.data_has_unconnected, self.logger),
                local_addr=(self.client_address, 0), family=socket.AF_INET, proto=socket.IPPROTO_UDP
            )
        server = (self.server_address, self.command_port)
        self.cmd_transport, self.cmd_protocol = await loop.create_datagram_endpoint(
            lambda: CommandProtocol(server, not self.use_multicast,
                                    self._data_callback, self.command_has_unconnected,
                                    self.logger),
            local_addr=(self.client_address, 0))

        self.server_info = await self.cmd_protocol.connect(timeout)
        if not self.server_info:
            return False
        vs = self.server_info.nat_net_stream_version_server
        self.cmd_protocol.version = (vs[0], vs[1])
        self.description = await self.cmd_protocol.get_description(timeout)
        if not self.description:
            return False
        self.rigid_body_names = {
            rb.new_id: rb.name for rb
            in self.description.rigid_bodies}
        self.cmd_protocol.init_keep_alive()
        self.logger.debug("NatNet client connected")
        return True

    def connect(self, timeout: float = 5.0) -> bool:
        if self._loop:
            return False
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(self.connect_async(timeout, loop=self._loop))

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
        self.server_info = None
        self.description = None
        self.rigid_body_names = {}

    def _has_unconnected(self, future: asyncio.Future[None]) -> None:
        self._unconnect()

    async def unconnect_async(self) -> None:
        self._unconnect()
        await asyncio.wait(
            [self.data_has_unconnected, self.command_has_unconnected])

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
        await asyncio.wait(
            [self.data_has_unconnected, self.command_has_unconnected],
            return_when=asyncio.FIRST_COMPLETED)

    async def get_data_async(self, timeout: float = 1.0) -> Optional[protocol.MoCapData]:
        if self._queue:
            if timeout > 0:
                try:
                    return await asyncio.wait_for(self._queue.get(), timeout)
                except asyncio.exceptions.TimeoutError:
                    self.logger.warning("Timed out")
                    return None
            return await self._queue.get()
        self.logger.error("No queue")
        return None

    def get_data(self, timeout: float = 0.0) -> Optional[protocol.MoCapData]:
        if self._loop:
            return self._loop.run_until_complete(self.get_data_async(timeout))
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
