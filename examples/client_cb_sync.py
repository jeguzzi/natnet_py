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
    logging.info("Connecting NatNet server ...")
    if client.connect(server_address=args.server, discovery_address=args.discovery,
        timeout=5.0, start_listening_for_data=False):
        logging.info("Connected NatNet server")
        if not client.start_listening_for_data():
            logging.warning("Failed starting listening")
        else:
            if not args.silent:
                client.data_callback = data_callback(client)
        if not client.wait(duration=args.duration):
            logging.warning("Failed running")
    else:
        logging.warning("Failed connecting NatNet server")
    logging.info("Unconnecting NatNet server ...")
    client.unconnect()
    logging.info("Unconnected NatNet server")
    client.close()


if __name__ == "__main__":
    main()
