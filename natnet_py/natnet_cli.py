import cmd
import logging
import argparse
from typing import Any
import netifaces

from natnet_py import SyncClient


def init_logging() -> None:
    FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(format=FORMAT)


def set_log_level(level_name: str) -> None:
    logging.getLogger().setLevel(logging.getLevelName(level_name))


def parser(args: Any = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server", default="", help="The server address to connect to.")
    parser.add_argument(
        "--client", default="0.0.0.0", help="The client address to bind to.")
    parser.add_argument(
        "--queue", default=10, type=int, help="The length of the data queue.")
    parser.add_argument(
        "--discovery", default="",
        help="The broadcast address to announce this client")
    parser.add_argument(
        "--iface", default="",
        help=("The network interface. When provided it will fill the client "
              "and the discovery address automatically"))
    parser.add_argument(
        "--log_level", default="INFO",
        help="The log level: one of DEBUG, INFO, WARNING, ERROR")
    parser.add_argument(
        "--no_sync", action='store_true',
        help="Add to disable clock synchronization")
    return parser


def parse(args: Any = None) -> argparse.Namespace:
    args = parser(args).parse_args()
    if args.iface:
        addrs = netifaces.ifaddresses(args.iface)
        if addrs:
            net = addrs[netifaces.AF_INET][0]
            args.client = net["addr"]
            if "broadcast" in net:
                args.discovery = net["broadcast"]
    return args  # type: ignore


class CmdShell(cmd.Cmd):
    intro = 'NatNet Client CLI. Type help or ? to list commands.\n'
    prompt = '(natnet) '
    file = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        args = parse()
        set_log_level(args.log_level)
        self.client = SyncClient(
            address=args.client, queue=args.queue, sync=not args.no_sync)
        print(self.client._loop)
        if args.discovery or args.server:
            self.client.connect(
                discovery_address=args.discovery, server_address=args.server)
            self.update_prompt()

    def update_prompt(self) -> None:
        server = self.client.server_address
        if server is not None:
            self.prompt = f'(natnet {server[0]}:{server[1]}) '
        else:
            self.prompt = '(natnet) '

    def do_discover(self, arg):
        'Discover servers: discover ADDRESS MAX_NUMBER'
        args = arg.split(" ")
        if len(args) == 0:
            address = '255.255.255.255'
        else:
            address = args[0]
        if len(args) > 1:
            number = int(args[1])
        else:
            number = 1
        servers = self.client.discover(address, number=number)
        print(servers)

    def do_connect(self, arg):
        'Discover servers: connect ADDRESS'
        if not arg:
            print("*** Please provide the server address")
            return
        self.client.connect(server_address=arg)
        self.update_prompt()

    def do_disconnect(self, arg):
        'Disconnect the server'
        self.client.unconnect()
        self.prompt = '(natnet) '

    def do_quit(self, arg):
        'Exit '
        return True

    def do_describe(self, arg):
        'Print the MoCap description'
        print(self.client.description)

    def do_data(self, arg):
        'Print the latest data'
        args = arg.split(" ")
        if len(args) > 0:
            last = bool_from_string(args[0])
        else:
            last = False
        data = self.client.get_data(last=last)
        if data:
            print(f"{data[0]}: {data[1]}")

    def do_log_level(self, arg):
        "Set the log level: log_level LEVEL"
        set_log_level(arg)

    def do_delay(self, arg):
        "Compute the latest data delay"
        args = arg.split(" ")
        if len(args) > 0:
            last = bool_from_string(args[0])
        else:
            last = False
        stamp, data = self.client.get_data(last=last)
        server_stamp = self.client.server_ticks_to_client_ns_time(
            data.suffix_data.stamp_camera_mid_exposure)
        print(f"Delay: {stamp - server_stamp} ns")

    def postloop(self):
        self.client.close()


def bool_from_string(value: str) -> bool:
    return value in set(("False", "F", "f", "false"))


def main():
    init_logging()
    CmdShell(completekey='tab').cmdloop()
