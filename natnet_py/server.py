# modified from https://github.com/mje-nz/python_natnet/blob/master/src/natnet/Server.py

import asyncio
import logging
import re
import socket
import struct
import time
from typing import Any, cast

from . import protocol


class Server:

    """A mock-up of a NatNet server that partially implements NatNet.

    Only used to test client code.

    Usage:

    >>> server = Server(60)
    >>> await srv.run()
    >>> server.close()

    """

    multicast_address = '239.255.42.100'
    data_port = 1511

    def __init__(self,
                 rate: int,
                 multicast: bool = False,
                 address: str = "127.0.0.1",
                 natnet_version: tuple[int, int] = (3, 1)):
        """
        Constructs a new instance.

        :param      rate:            The frame rate
        :param      multicast:       Whether to use multicasting
        :param      address:         The server address
        :param      natnet_version:  The server natnet version (major, minor)
        """
        self.clients: set[str] = set()
        self._rate = 1
        self.rate = rate
        self.multicast = multicast
        self.address = address
        self.frame_number = 0
        self.time_0 = time.time_ns()
        self.natnet_version = natnet_version
        protocol.set_version(*natnet_version)

    @property
    def rate(self) -> int:
        """The framerate"""
        return self._rate

    @rate.setter
    def rate(self, value: int) -> None:
        value = min(120, max(1, value))
        if value != self._rate:
            logging.getLogger().info(f"Set rate to {value}")
            self._rate = value

    def get_ns(self) -> int:
        return time.time_ns() - self.time_0

    async def run(self):
        """
        Run the server
        """
        loop = asyncio.get_running_loop()
        if self.multicast:
            self.multicast_sock = socket.socket(socket.AF_INET,
                                                socket.SOCK_DGRAM,
                                                socket.IPPROTO_UDP)
            self.multicast_sock.setsockopt(socket.SOL_SOCKET,
                                           socket.SO_REUSEADDR, 1)
            # self.multicast_sock.setsockopt(socket.IPPROTO_IP,
            #                                socket.IP_MULTICAST_TTL, 32)
        logging.info(f"Start server on {self.address}:1510")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 1510))
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: ServerProtocol(self),
            sock=sock,
            # local_addr=(self.address, 1510)
        )
        try:
            await self.stream_mocap_data()
        finally:
            self.close()

    def close(self):
        """Close the server"""
        if self.transport:
            logging.info("Stop server")
            self.transport.close()
        self.transport = None

    def add_client(self, address: str) -> None:
        if not self.multicast:
            if address not in self.clients:
                logging.getLogger().info(f"Add client at {address}")
                self.clients.add(address)

    def get_rigid_bodies_def(self) -> list[protocol.RigidBodyDescription]:
        """Overwrite to define the MoCap description"""
        return []

    def get_rigid_bodies_data(self) -> list[protocol.RigidBodyData]:
        """Overwrite to define the MoCap data"""
        return []

    def get_description(self) -> protocol.MoCapDescription:
        return protocol.MoCapDescription(
            rigid_bodies=self.get_rigid_bodies_def())

    def get_mocap_data(self) -> protocol.MoCapData:
        ns = self.get_ns()
        suffix_data = protocol.FrameSuffixData(timecode=0,
                                               timecode_sub=0,
                                               timestamp=time.time(),
                                               stamp_camera_mid_exposure=ns,
                                               stamp_data_received=ns,
                                               stamp_transmit=ns)
        self.frame_number += 1
        return protocol.MoCapData(frame_number=self.frame_number,
                                  rigid_bodies=self.get_rigid_bodies_data(),
                                  suffix_data=suffix_data)

    async def stream_mocap_data(self):
        while True:
            msg = self.get_mocap_data()
            data = protocol.pack(msg)
            if not self.multicast:
                for address in self.clients:
                    self.transport.sendto(data, (address, self.data_port))
            else:
                self.multicast_sock.sendto(
                    data, (self.multicast_address, self.data_port))
            await asyncio.sleep(1.0 / self.rate)


class ServerProtocol:

    def __init__(self, server: Server):
        self._server = server

    def connection_made(self, transport: asyncio.BaseTransport):
        self.transport = cast(asyncio.DatagramTransport, transport)
        sock = transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def connection_lost(self, exc: Any) -> None:
        logging.getLogger().warning("Server cmd socket closed")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        logging.getLogger().debug(
            f'Got {len(data)} bytes from {addr[0]}:{addr[1]}')
        request = protocol.unpack(protocol.Buffer(data))
        # logging.getLogger().debug(f'Received {request}')
        response: protocol.Msg | None = None
        if isinstance(request, protocol.ConnectRequest) or isinstance(
                request, protocol.DiscoveryRequest):
            response = self.get_server_info()
            self._server.add_client(addr[0])
        elif isinstance(request, protocol.EchoRequest):
            response = self.get_echo_response(request)
        elif isinstance(request, protocol.ModelDefRequest):
            response = self._server.get_description()
        elif isinstance(request, protocol.KeepAliveRequest):
            pass
        elif isinstance(request, protocol.Request):
            response = self.respond(request)
        else:
            logging.getLogger().error(f"Unknown request {request}")
        if response:
            self.transport.sendto(protocol.pack(response), addr)

    def respond(self,
                request: protocol.Request) -> protocol.Response | None:
        data = request.data.decode("ascii")
        if data == "FrameRate":
            return self.get_framerate()
        m = re.match(r"SetProperty,([^,]+),([^,]+),([^,]+)", data)
        if m:
            name, prop, value = m.groups()
            logging.getLogger().info(
                f"Set property {prop} of {name} to {value}")
            # Should set some properties
            return protocol.Response(data=b'\0' * 4)
        m = re.match(r"SetProperty,([^,]+),([^,]+)", data)
        if m:
            prop, value = m.groups()
            logging.getLogger().info(f"Set property {prop} to {value}")
            if prop == "Master Rate":
                self._server.rate = int(value)
            return protocol.Response(data=b'\0' * 4)
        m = re.match(r"GetProperty,([^,]+),([^,]+)", data)
        if m:
            name, prop = m.groups()
            logging.getLogger().info(f"Get property {prop} of {name}")
            if prop == 'Enabled' or prop == 'Active':
                return protocol.Response(data=b'\1')
            if prop == 'Name':
                buffer = protocol.WriteBuffer()
                buffer.write_string("?")
                return protocol.Response(buffer.data)
            logging.getLogger().warning(f"Unsupported property {prop}")
            return protocol.Response(data=b'\0' * 4)
        # logging.getLogger().error(f"Unknown request {request}")
        return None

    def get_server_info(self) -> protocol.ServerInfo:
        connection_info = protocol.ConnectionInfo(
            data_port=self._server.data_port,
            multicast=self._server.multicast,
            multicast_address=self._server.multicast_address)
        version = protocol.Version((*protocol.get_version(), 0, 0))
        return protocol.ServerInfo(application_name=u'python_natnet server',
                                   server_version=version,
                                   nat_net_stream_version_server=version,
                                   high_resolution_clock_frequency=1000000000,
                                   connection_info=connection_info)

    def get_echo_response(
            self, request: protocol.EchoRequest) -> protocol.EchoResponse:
        return protocol.EchoResponse(request_stamp=request.timestamp,
                                     received_stamp=self._server.get_ns())

    def get_framerate(self) -> protocol.Response:
        return protocol.Response(data=struct.pack("<f", self._server.rate))
