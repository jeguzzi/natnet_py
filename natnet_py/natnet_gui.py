import asyncio
import json
import logging
import sys
from typing import Any
import webbrowser
import os
import argparse

import websockets
import websockets.server

import numpy as np
import quaternion  # type: ignore

from natnet_py import AsyncClient
from natnet_py.protocol import MoCapData, MoCapDescription


async def producer_handler(
        websocket: websockets.server.WebSocketServerProtocol,
        queue: asyncio.Queue) -> None:
    while True:
        msg = await queue.get()
        try:
            await websocket.send(msg)
        except websockets.exceptions.ConnectionClosed:
            pass


Msg = dict[str, tuple[bool, float, float, float, float, float, float]]


def msg(data: MoCapData, description: MoCapDescription | None) -> Msg:
    rbs: Msg = {}
    for rb, desc in zip(data.rigid_bodies, description.rigid_bodies):
        q = np.quaternion(*rb.orientation)
        rpy = [float(value) for value in quaternion.as_euler_angles(q)]
        rbs[desc.name] = (rb.tracking_valid, *rb.position, *rpy)
    return rbs


def parser(args: Any = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    return parser

class WebUI:

    def __init__(self,
                 client: AsyncClient,
                 host: str = '0.0.0.0',
                 port: int = 8000,
                 max_rate: float = 30):
        """
        Constructs a new instance.

        :param      host:                The host address serving the HTML page.
        :param      port:                The port serving the HTML page.
        :param      max_rate:            The maximum synchronization rate [fps]
        """
        self.port = port
        self.host = host
        self.queues: list[asyncio.Queue] = []
        if max_rate > 0:
            self.min_period = 1.0 / max_rate
        else:
            self.min_period = 0
        self.last_update_stamp: int = 0
        self._prepared = False
        self.server: websockets.WebSocketServer | None = None
        self._client = client

    async def run(self) -> None:
        if not await self.prepare():
            return
        while True:
            data = await self._client.get_data()
            if data:
                await self.send(msg(data[1], self._client.description))
                await asyncio.sleep(self.min_period)
        await self.stop()

    async def prepare(self) -> bool:
        try:
            self.server = await websockets.server.serve(
                self.handle_ws, self.host, self.port)
            return True
        except OSError as e:
            print(e, file=sys.stderr)
            return False

    async def handle_ws(self,
                        websocket: websockets.server.WebSocketServerProtocol,
                        path: str,
                        port: int = 8000) -> None:
        logging.info('Websocket connection opened')
        queue: asyncio.Queue = asyncio.Queue()
        self.queues.append(queue)
        producer_task = asyncio.ensure_future(
            producer_handler(websocket, queue))
        done, pending = await asyncio.wait([producer_task],
                                           return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        self.queues.remove(queue)
        logging.info('Websocket connection closed')

    async def send(self, msg: Any) -> None:
        data = json.dumps(msg)
        for queue in self.queues:
            await queue.put(data)

    async def stop(self) -> None:
        logging.info('Stopping UI')
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.server = None
        self._prepared = False
        logging.info('Stopped')

    def __del__(self):
        if self.server:
            self.server.close()


async def run(args: Any = None) -> None:
    _ = parser().parse_args()
    client = AsyncClient(queue=1)
    connected = await client.connect(discovery_address="255.255.255.255")
    if connected:
        ui = WebUI(client)
        await ui.run()
    await client.close()


def open_html() -> None:
    file = os.path.join(os.path.dirname(__file__), 'gui.html')
    webbrowser.open(f"file://{file}", new=1)


def main(args: Any = None) -> None:
    open_html()
    asyncio.run(run())


if __name__ == "__main__":
    main()
