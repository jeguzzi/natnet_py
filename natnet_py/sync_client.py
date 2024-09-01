import logging
import asyncio
import time
from threading import Thread, current_thread
from functools import wraps
from typing import Callable

from . import protocol
from .async_client import AsyncClient, DataCallback


def block(f):

    method = getattr(AsyncClient, f.__name__)

    @wraps(method)
    def g(self, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(
            method(self._client, *args, **kwargs), self._loop)
        result = future.result()
        f(self, *args, **kwargs)
        return result

    return g


def client(f):

    method = getattr(AsyncClient, f.__name__)

    try:
        method = method.fget
    except AttributeError:
        ...

    @wraps(method)
    def g(self, *args, **kwargs):
        return method(self._client, *args, **kwargs)

    return g


class SyncClient(Thread):
    """
    This class describes a Natnet client.

    Usage:

    1. Create the client

       >>> client = SyncClient()

    2. Discover a server

       >>> servers = client.discover(broadcast_address=255.255.255.255, timeout=1)

    3. and/or connect to a server directly

       >>> client.connect(server_address=127.0.0.1)

    3. Read data

       >>> client.get_data()

       or add a callback

       >>> client.data_callback = lambda time_ns, msg: print(time_ns, msg)

    4. and/or wait for some time or until disconnection

       >>> client.wait(duration=60.0)

    5. close the connection

       >>> client.unconnect()

    6. close the client

       >>> client.close()

    """
    def __init__(
        self,
        address: str = "0.0.0.0",
        command_port: int = 1510,
        queue: int = 10,
        logger: logging.Logger = logging.getLogger(),
        now: Callable[[], int] = time.time_ns,
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
        super().__init__()
        self._client = AsyncClient(
            address=address, command_port=command_port, queue=queue,
            logger=logger, now=now, sync=sync)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self.start()

    def run(self):
        """
        :meta private:
        """
        self.tid = current_thread()
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
        self._client.logger.info('Closed')

    @property
    @client
    def server_address(self) -> tuple[str, int] | None:  # type: ignore[empty-body]
        ...

    @property
    @client
    def server_info(self) -> protocol.ServerInfo | None:  # type: ignore[empty-body]
        ...

    @server_info.setter
    def server_info(self, value: protocol.ServerInfo) -> None:  # type: ignore[empty-body]
        self._client.server_info = value

    @property
    @client
    def description(self) -> protocol.MoCapDescription | None:  # type: ignore[empty-body]
        ...

    @description.setter
    def description(self, value: protocol.MoCapDescription | None) -> None:
        self._client.description = value

    @property
    @client
    def data_callback(self) -> DataCallback | None:  # type: ignore[empty-body]
        ...

    @data_callback.setter
    def data_callback(self, value: DataCallback | None) -> None:
        self._client.data_callback = value

    @property
    @client
    def rigid_body_names(self) -> dict[int, str]:  # type: ignore[empty-body]
        ...

    @property
    @client
    def use_multicast(self) -> bool:  # type: ignore[empty-body]
        ...

    @property
    @client
    def multicast_address(self) -> str:  # type: ignore[empty-body]
        ...

    @property
    @client
    def data_port(self) -> int:  # type: ignore[empty-body]
        ...

    @property
    @client
    def can_change_bitstream_version(self) -> bool:  # type: ignore[empty-body]
        ...

    @property
    @client
    def can_subscribe(self) -> bool:  # type: ignore[empty-body]
        ...

    @property
    @client
    def connected(self) -> bool:  # type: ignore[empty-body]
        ...

    @client
    def server_ticks_to_client_ns_time(self, ticks: int) -> int:  # type: ignore[empty-body]
        ...

    @block
    def send_request(
        self, data: bytes, timeout: float = 0.0
    ) -> protocol.Response | None:  # type: ignore[empty-body]
        ...

    @block
    def get_data(
        self, timeout: float = 0.0, last: bool = False
    ) -> tuple[int, protocol.MoCapData] | None:  # type: ignore[empty-body]
        ...

    @block
    def discover(  # type: ignore
        self,
        broadcast_address: str,
        number: int = -1,
        timeout: float = 5.0
    ) -> dict[tuple[str, int], protocol.ServerInfo]:
        ...

    @block
    def connect(  # type: ignore[empty-body]
        self,
        discovery_address: str = '',
        server_address: str = '127.0.0.1',
        timeout: float = 5.0,
        start_listening_for_data: bool = True
    ) -> bool:
        ...

    @block
    def start_listening_for_data(self, timeout: float = 5.0) -> bool:  # type: ignore[empty-body]
        ...

    @block
    def wait(self, duration: float) -> bool:  # type: ignore[empty-body]
        ...

    @block
    def unconnect(self) -> None:
        ...

    @block
    def close(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self.join()
