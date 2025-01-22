import argparse
import asyncio
from typing import TypedDict

import yaml

from natnet_py import protocol, server
from natnet_py.utils import init_logging, set_log_level


class RigidBodyConfig(TypedDict):
    name: str
    position: tuple[float, float, float]
    orientation: tuple[float, float, float, float]


description = "Dummy NatNet Server"

RigidBodiesConfig = dict[int, RigidBodyConfig]

default_rigid_bodies: RigidBodiesConfig = {
    0: {
        'name': 'rb0',
        'position': (1.1, 2.2, 3.3),
        'orientation': (0.5, 0.5, 0.5, 0.5)
    },
    1: {
        'name': 'rb1',
        'position': (-1.1, 2.2, -3.3),
        'orientation': (0.5, -0.5, 0.5, -0.5)
    }
}


def init_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--address", default="0.0.0.0")
    parser.add_argument("--multicast", action='store_true')
    parser.add_argument("--log_level", default="INFO")
    parser.add_argument("--rate", default=30.0, type=float)
    parser.add_argument("--major", default=3, type=int)
    parser.add_argument("--minor", default=1, type=int)
    parser.add_argument("--rigid_bodies", default="", type=str)


class MyServer(server.Server):

    def __init__(self,
                 rate: int,
                 multicast: bool = False,
                 address: str = "127.0.0.1",
                 natnet_version: tuple[int, int] = (3, 1),
                 rigid_bodies: RigidBodiesConfig = {}) -> None:
        super().__init__(rate=rate,
                         multicast=multicast,
                         address=address,
                         natnet_version=natnet_version)
        self.rigid_bodies = rigid_bodies

    def get_rigid_bodies_data(self) -> list[protocol.RigidBodyData]:
        return [
            protocol.RigidBodyData(id=_id,
                                   position=rb['position'],
                                   orientation=rb['orientation'],
                                   tracking_valid=True,
                                   error=1e-4)
            for _id, rb in self.rigid_bodies.items()
        ]

    def get_rigid_bodies_def(self) -> list[protocol.RigidBodyDescription]:
        return [
            protocol.RigidBodyDescription(name=rb['name'], id=_id)
            for _id, rb in self.rigid_bodies.items()
        ]


async def run(args: argparse.Namespace) -> None:
    if args.rigid_bodies:
        with open(args.rigid_bodies) as f:
            rigid_bodies = yaml.safe_load(f.read())
    else:
        rigid_bodies = default_rigid_bodies
    init_logging()
    set_log_level(args.log_level)
    srv = MyServer(rate=args.rate,
                   multicast=args.multicast,
                   address=args.address,
                   natnet_version=(args.major, args.minor),
                   rigid_bodies=rigid_bodies)
    try:
        await srv.run()
    except KeyboardInterrupt:
        srv.close()
        pass


def _main(args: argparse.Namespace) -> None:
    asyncio.run(run(args))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    init_parser(p)
    return p


def main():
    _main(parser().parse_args())
