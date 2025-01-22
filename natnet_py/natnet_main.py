from __future__ import annotations

import argparse
from typing import Any
from types import ModuleType

from . import natnet_cli, natnet_discover, natnet_dummy, natnet_dump, natnet_gui


def config_parser(parsers: Any, name: str, module: ModuleType) -> None:
    parser = parsers.add_parser(name, help=module.description)
    module.init_parser(parser)
    parser.set_defaults(func=module._main)


def init_parser(parser: argparse.ArgumentParser) -> None:
    parsers = parser.add_subparsers(dest='cmd', title='Subcommands')
    config_parser(parsers, 'client', natnet_cli)
    config_parser(parsers, 'discover', natnet_discover)
    config_parser(parsers, 'dummy', natnet_dummy)
    config_parser(parsers, 'dump', natnet_dump)
    config_parser(parsers, 'gui', natnet_gui)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='natnet')
    init_parser(p)
    return p


def main() -> None:
    p = parser()
    args = p.parse_args()
    if args.cmd is not None:
        args.func(args)
    else:
        print("Welcome to natnet!\n")
        p.print_help()
