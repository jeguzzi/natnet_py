import logging
from typing import Any

from natnet_py import SyncClient
from utils import data_callback, parse, init_logging


def main(args: Any = None) -> None:
    args = parse()
    init_logging(args.log_level)
    client = SyncClient(
        address=args.client,
        queue=10,
        sync=not args.no_sync
    )
    connected = client.connect(
        timeout=5.0, server_address=args.server,
        discovery_address=args.discovery)
    if connected:
        if not args.silent:
            cb = data_callback(client)
            for i in range(10):
                data = client.get_data(timeout=2.0)
                if data:
                    cb(*data)
                else:
                    break
    client.unconnect()
    client.close()


if __name__ == "__main__":
    main()
