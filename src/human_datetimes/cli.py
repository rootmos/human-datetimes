import argparse
import logging
import os
import sys
from typing import Callable

from . import env, package_version, utils, whoami
from . import human_datetimes

try:
    import argcomplete
    with_argcomplete = True
except ImportError:
    with_argcomplete = False

logger = logging.getLogger(__name__)

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs["add_help"] = False
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = argparse.ArgumentDefaultsHelpFormatter
        super().__init__(*args, **kwargs)
        self.register("type", "datetime", human_datetimes.local)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def parse_args(build: Callable[[], argparse.ArgumentParser]) -> argparse.Namespace:
    def add_common_options(p, add_help=None):
        assert whoami is not None

        g = p.add_argument_group("common options")
        g.add_argument("-v", "--version", action="version", version=f"{whoami} {package_version}")
        if with_argcomplete:
            g.add_argument("--completion-script", action="store_true", help="print script that when sourced configures shell completion, then exit", default=argparse.SUPPRESS)
        p.add_argument("-L", "--log", default=env("LOG_LEVEL", "INFO"), help="set log level")
        if add_help:
            g.add_argument("-h", "--help", action='help', default=argparse.SUPPRESS, help="show this help message and exit")

    early_parser = ArgumentParser()
    add_common_options(early_parser, add_help=False)
    args, _ = early_parser.parse_known_args()

    utils.setup_logger(args.log)
    logger.debug("early args: %s", args)

    if with_argcomplete and vars(args).get("completion_script"):
        prog = os.path.basename(sys.argv[0])
        sys.stdout.write(argcomplete.shellcode([ prog ])) # pyright: ignore [ reportPrivateImportUsage ]
        sys.exit(0)

    main_parser = build()
    add_common_options(main_parser, add_help=True)

    if with_argcomplete:
        argcomplete.autocomplete(main_parser)
    return main_parser.parse_args(namespace=args)

def main_parser():
    parser = ArgumentParser() # description="TODO"

    parser.add_argument("human_string", metavar="HUMAN_DATETIME")

    parser.add_argument("-n", "--now", type="datetime", help="resolve datetimes relative to NOW")

    bias = parser.add_mutually_exclusive_group()
    bias.add_argument("-b", "--bias", metavar="BIAS", choices=["future", "past"], help="prefer datetimes from the future or the past")
    bias.add_argument("-f", "--future", dest="bias", action="store_const", const="future")
    bias.add_argument("-p", "--past", dest="bias", action="store_const", const="past")

    return parser

def main():
    args = parse_args(main_parser)
    logger.debug("args: %s", args)

    dt = human_datetimes.local(
        human_string = args.human_string,
        bias = args.bias,
        now = args.now,
    )
    print(dt.isoformat(timespec="seconds"))
