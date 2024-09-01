import logging
from typing import Any

from natnet_py import SyncClient
from utils import data_callback, parse, init_logging


def main(args: Any = None) -> None:
    args = parse()
    init_logging(args.log_level)
    client = SyncClient(
        address=args.client,
        queue=-1,
        sync=not args.no_sync
    )
    if client.connect(server_address=args.server, discovery_address=args.discovery,
        timeout=5.0, start_listening_for_data=False):
        if client.start_listening_for_data():
            if not args.silent:
                client.data_callback = data_callback(client)
        _ = client.wait(duration=args.duration):
    client.unconnect()
    client.close()


if __name__ == "__main__":
    main()
