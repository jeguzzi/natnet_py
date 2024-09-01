import argparse
import logging
import netifaces
from typing import Any, Callable, Protocol
from natnet_py.protocol import MoCapData


class Client(Protocol):

    @property
    def rigid_body_names(self) -> dict[int, str]:
        ...


def data_callback(client: Client) -> Callable[[int, MoCapData], None]:

    def cb(time_ns: int, data: MoCapData) -> None:
        rbs = client.rigid_body_names
        if not data:
            return
        if data.suffix_data:
            f = data.suffix_data.stamp_data_received
        else:
            f = -1
        logging.info(f"@{f}:")
        for rb in data.rigid_bodies:
            logging.info(
                f"\t{rbs.get(rb.id, '?')}, {rb.tracking_valid}, {rb.error:.1E}, "
                f"{rb.position}, {rb.orientation}"
            )

    return cb


def parse(args: Any = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="")
    parser.add_argument("--client", default="0.0.0.0")
    parser.add_argument("--discovery", default="255.255.255.255")
    parser.add_argument("--multicast", default=False, type=bool)
    parser.add_argument("--iface", default="")
    parser.add_argument("--log_level", default="INFO")
    parser.add_argument("--silent", action='store_true')
    parser.add_argument("--no_sync", action='store_true')
    parser.add_argument("--timeout", default=1.0, type=float)
    parser.add_argument("--duration", default=2.0, type=float)
    args = parser.parse_args(args)
    if args.iface:
        addrs = netifaces.ifaddresses(args.iface)
        if addrs:
            net = addrs[netifaces.AF_INET][0]
            args.client = net["addr"]
            if "broadcast" in net:
                args.broadcast = net["broadcast"]
    return args  # type: ignore


def init_logging(level_name: str = "INFO") -> None:
    FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(format=FORMAT)
    logging.getLogger().setLevel(logging.getLevelName(level_name))
