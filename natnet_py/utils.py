from __future__ import annotations

import logging


def init_logging() -> None:
    FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(format=FORMAT)


def set_log_level(level_name: str) -> None:
    logging.getLogger().setLevel(logging.getLevelName(level_name))

