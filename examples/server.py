import argparse
import asyncio
from typing import Any

from natnet_py import protocol, server

from utils import init_logging

rigid_bodies = {
    0: ('rb0', (1.1, 2.2, 3.3), (0.5, 0.5, 0.5, 0.5)),
    1: ('rb1', (-1.1, 2.2, -3.3), (0.5, -0.5, 0.5, -0.5))
}


def parse(args: Any = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default="0.0.0.0")
    parser.add_argument("--multicast", action='store_true')
    parser.add_argument("--log_level", default="INFO")
    parser.add_argument("--rate", default=30.0, type=float)
    parser.add_argument("--major", default=3, type=int)
    parser.add_argument("--minor", default=1, type=int)
    args = parser.parse_args(args)
    return args  # type: ignore


class MyServer(server.Server):

    def get_rigid_bodies_data(self) -> list[protocol.RigidBodyData]:
        return [
            protocol.RigidBodyData(id=_id,
                                   position=p,
                                   orientation=q,
                                   tracking_valid=True,
                                   error=1e-4)
            for _id, (name, p, q) in rigid_bodies.items()
        ]

    def get_rigid_bodies_def(self) -> list[protocol.RigidBodyDescription]:
        return [
            protocol.RigidBodyDescription(name=name, id=_id)
            for _id, (name, *_) in rigid_bodies.items()
        ]


if __name__ == '__main__':
    args = parse()
    init_logging(args.log_level)
    srv = MyServer(rate=args.rate,
                   multicast=args.multicast,
                   address=args.address,
                   natnet_version=(args.major, args.minor))
    try:
        asyncio.run(srv.run())
    except KeyboardInterrupt:
        srv.close()
        pass
