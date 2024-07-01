# largely inspired by https://github.com/mje-nz/python_natnet/blob/master/src/natnet/comms.py

import time
import logging
import asyncio
from typing import TYPE_CHECKING, Tuple, Optional, Callable

from . import protocol

if TYPE_CHECKING:
    from . import client

# All time units are in nanoseconds
# dt_s = (1 + beta) * dt_c


class SynchronizedClock:
    def __init__(
        self,
        cmd: "client.CommandProtocol",
        server_info: protocol.ServerInfo,
        logger: logging.Logger,
        estimate_skew: bool = False,
        period: float = 500.0,
        now: Callable[[], int] = time.time_ns,
    ) -> None:
        self._cmd = cmd
        self._freq = server_info.high_resolution_clock_frequency  # ticks / s
        self.count = 0
        self._t0_c = 0  # ns
        self._t2_c = 0  # ns
        self._t2_s = 0  # ns
        self._min_rtt = 1e9  # ns
        self._beta = 0.0
        self._task: Optional[asyncio.Task[None]] = None
        self.logger = logger
        self.estimate_skew = estimate_skew
        self._period = period
        self._now_ns = now

    def init(self) -> None:
        self.logger.debug("Init clock")
        self._task = asyncio.create_task(self._run())

    def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        self.logger.info("Start initial clock sync")
        while self.count < 10:
            await self.echo()
        self.logger.info(
            f"Initial clock sync done: min_rtt {self._min_rtt} ns, beta {self._beta}, delta {self._t2_c - self._t2_s}"
        )
        while True:
            await asyncio.sleep(self._period)
            await self.echo()

    def ticks_to_nanoseconds(self, ticks: int) -> int:
        return int(1e9 * ticks / self._freq)

    async def echo(self) -> None:
        self._t0_c = self._now_ns()
        self.logger.debug(f"<- Echo {self.count}: client time {self._t0_c}")
        response = await self._cmd.send_echo(self._t0_c, timeout=0.5)
        t2_c = self._now_ns()
        if not response:
            return
        if response.request_stamp != self._t0_c:
            self.logger.warning(
                f"Echo response {response} does not match request {self._t0_c}"
            )
            return
        self.update(
            t0_c=self._t0_c,
            t2_c=t2_c,
            t1_s=self.ticks_to_nanoseconds(response.received_stamp),
        )
        self.count += 1

    def update(self, t0_c: int, t1_s: int, t2_c: int) -> None:
        rtt = t2_c - t0_c
        if not self._t2_s:
            # First echo, initialize
            self._t2_s = t1_s + int((1 + self._beta) * rtt / 2)
            self._t2_c = t2_c
            self.logger.debug(
                f"-> Echo {self.count: 5d}: client time {self._t0_c} -- {self._t2_c}, server time {self._t2_s}"
            )
        else:
            dt_c = t2_c - self._t2_c
            # Assume beta is severe and we have a bad estimate of it
            rtt_threshold = self._min_rtt + max(1e5, dt_c * 5e5)
            if rtt < rtt_threshold:
                # t2_s = dt_c * (1 + beta_old) + t2_s_old
                t2_s = self.client_to_server_time(t2_c)
                self._t2_s = t1_s + int((1 + self._beta) * rtt / 2)
                self._t2_c = t2_c
                # delta = self._t2_s - t2_s
                #       = dt_s - dt_c * (1 + beta_old)
                #       = dt_c * ((1 + beta) - (1 + beta_old))
                #       = dt_c * (beta - beta_old)
                # => beta = delta / dt_c + beta_old
                # This only works over a reasonably long time period
                if self.estimate_skew and dt_c > 1e9:
                    delta = self._t2_s - t2_s
                    drift = delta / dt_c
                    if not self._beta:
                        # Initialize
                        self._beta = drift
                    else:
                        # Slowly converge on the true beta
                        self._beta += drift / 2
                    self.logger.debug(
                        f"correction {delta} ns, drift {drift}, new beta: {self._beta}"
                    )
                self.logger.debug(
                    f"-> Echo {self.count}: client time {self._t0_c} -- {self._t2_c}, server time {self._t2_s}"
                    f", RTT {rtt} (min {self._min_rtt}), dt {dt_c}"
                )

        if rtt < self._min_rtt:
            self._min_rtt = rtt

    def server_ticks_to_client_time(self, ticks: int) -> int:
        t_s = self.ticks_to_nanoseconds(ticks)
        return int(self._t2_c + (t_s - self._t2_s) / (1 + self._beta))

    def client_to_server_time(self, t_c: int) -> int:
        return int(self._t2_s + (t_c - self._t2_c) * (1 + self._beta))

    def compute_latencies(
        self, data: protocol.FrameSuffixData, t_c: int
    ) -> Tuple[int, int]:
        system_latency_ticks = data.stamp_transmit - data.stamp_camera_mid_exposure
        system_latency = self.ticks_to_nanoseconds(system_latency_ticks)
        transmit_latency = t_c - self.server_ticks_to_client_time(data.stamp_transmit)
        return system_latency, transmit_latency

    def compute_acquisition_stamp(self, data: protocol.FrameSuffixData) -> int:
        return self.server_ticks_to_client_time(data.stamp_camera_mid_exposure)
