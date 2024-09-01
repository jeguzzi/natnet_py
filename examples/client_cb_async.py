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
        queue=-1,
        sync=not args.no_sync
    )
    logging.info(f"Connecting NatNet server ... {args}")

    if await client.connect(server_address=args.server,
        discovery_address=args.discovery, timeout=args.timeout,
        start_listening_for_data=False):
        logging.info("Connected NatNet server")
        await client.start_listening_for_data()
        if not args.silent:
            client.data_callback = data_callback(client)
        await client.wait(duration=args.duration)
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
