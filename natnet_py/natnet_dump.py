import logging
import argparse
from typing import Any
import netifaces
import h5py
import asyncio
import numpy as np
from collections import defaultdict

from natnet_py import AsyncClient
from natnet_py.protocol import RigidBodyData


def init_logging() -> None:
    FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(format=FORMAT)


def set_log_level(level_name: str) -> None:
    logging.getLogger().setLevel(logging.getLevelName(level_name))


def parser(args: Any = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="The HDF5 output file path")
    parser.add_argument(
        "--server", default="", help="The server address to connect to.")
    parser.add_argument(
        "--discovery", default="255.255.255.255",
        help="The broadcast address to announce this client")
    parser.add_argument(
        "--iface", default="",
        help=("The network interface. When provided it will fill the client "
              "and the discovery address automatically"))
    parser.add_argument(
        "--log_level", default="INFO",
        help="The log level: one of DEBUG, INFO, WARNING, ERROR")
    parser.add_argument(
        "--duration", default=0, type=float,
        help="Record duration in seconds. Set to zero or negative to ignore.")
    return parser


def parse(args: Any = None) -> argparse.Namespace:
    args = parser(args).parse_args()
    if args.iface:
        addrs = netifaces.ifaddresses(args.iface)
        if addrs:
            net = addrs[netifaces.AF_INET][0]
            args.client = net["addr"]
            if "broadcast" in net:
                args.discovery = net["broadcast"]
    return args  # type: ignore


async def run() -> None:
    init_logging()
    args = parser().parse_args()
    set_log_level(args.log_level)
    client = AsyncClient(queue=0)
    connected = await client.connect(discovery_address=args.discovery, server_address=args.server)
    restamp = False
    rbs: dict[int, list[tuple[int, RigidBodyData]]] = defaultdict(list)

    def collect(stamp, data) -> None:
        if not restamp:
            stamp = client.server_ticks_to_client_ns_time(
                data.suffix_data.stamp_camera_mid_exposure)
        for rb in data.rigid_bodies:
            rbs[rb.id].append((stamp, rb))

    if connected:
        client.logger.info("Collecting data ...")
        client.data_callback = collect
        await client.wait(args.duration)
    await client.close()
    if not rbs:
        client.logger.info("Collected no data")
        return
    client.logger.info("Collected data")
    with h5py.File(args.output, "w") as f:
        client.logger.info(f"Saving data to {args.output} ...")
        for i, data in rbs.items():
            name = client.rigid_body_names.get(i, str(i))
            g = f.create_group(f"rigid_bodies/{name}")
            ds = g.create_dataset("position", data=np.array([msg.position for _, msg in data]))
            ds.attrs['unit'] = 'mm'
            ds.attrs['coords'] = 'x, y, z'
            ds = g.create_dataset("orientation", data=np.array([msg.orientation for _, msg in data]))
            ds.attrs['coords'] = 'x, y, z, w'
            ds = g.create_dataset("error", data=np.array([msg.error for _, msg in data]))
            ds.attrs['unit'] = 'mm'
            ds = g.create_dataset("time", data=np.array([stamp for stamp, _ in data]))
            ds.attrs['unit'] = 'ns'
            ds = g.create_dataset("tracked", data=np.array([msg.tracking_valid for _, msg in data]))
        client.logger.info("Saved data")


def main(args: Any = None) -> None:
    asyncio.run(run())
