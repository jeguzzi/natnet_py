from __future__ import annotations

import argparse
import asyncio

from natnet_py import AsyncClient
from natnet_py.utils import init_logging, set_log_level

description = "Discover NatNet Servers"


def init_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--address", default="255.255.255.255",
        help="The broadcast address to announce this client")
    parser.add_argument(
        "--log_level", default="ERROR",
        help="The log level: one of DEBUG, INFO, WARNING, ERROR")
    parser.add_argument(
        "--timeout", default=1.0, type=float, help="Timeout in seconds")
    parser.add_argument(
        "--number", default=1, type=int,
        help="How many servers to discover")


async def run(args: argparse.Namespace) -> None:
    init_logging()
    set_log_level(args.log_level)
    client = AsyncClient()
    servers = await client.discover(
        broadcast_address=args.address,
        timeout=args.timeout, number=args.number)
    for (ip, port), info in servers.items():
        version = '.'.join(map(str, info.nat_net_stream_version_server.value))
        c_info = info.connection_info
        print('-'* 60)
        print(f"{ip}:{port}")
        print(f"\t{info.application_name} using NatNet version {version}")
        if c_info:
            if c_info.multicast:
                print(f"\tmulticast data stream on {c_info.multicast_address}:{c_info.data_port}")
            else:
                print(f"\tunicast data stream on :{c_info.data_port}")
        print('-'* 60)
        print()
    await client.close()


def _main(args: argparse.Namespace) -> None:
    asyncio.run(run(args))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    init_parser(p)
    return p


def main():
    _main(parser().parse_args())
