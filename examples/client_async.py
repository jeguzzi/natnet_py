import logging
import asyncio
from typing import Any

from natnet_py import AsyncClient
from utils import data_callback, parse, init_logging


async def run(args: Any = None) -> None:
    args = parse()
    init_logging(args.log_level)
    client = AsyncClient(
        address=args.client,
        queue=10,
        sync=not args.no_sync
    )
    logging.info("Connecting NatNet server ...")
    connected = await client.connect(
        timeout=5.0, server_address=args.server,
        discovery_address=args.discovery)
    if connected:
        logging.info("Connected NatNet server")
        if not args.silent:
            cb = data_callback(client)
            for i in range(10):
                data = await client.get_data(timeout=2.0)
                if data:
                    cb(*data)
                else:
                    break
    else:
        logging.warning("Failed connecting NatNet server")
    logging.info("Unconnecting NatNet server ...")
    await client.unconnect()
    logging.info("Unconnected NatNet server")
    await client.close()


def main(args: Any = None) -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
