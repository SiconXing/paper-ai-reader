import dotenv

dotenv.load_dotenv()

import argparse

from fetch.cli import add_fetch_arguments, execute_fetch
from load.cli import add_loader_arguments, execute_loader
from read.cli import add_read_arguments, execute_read


def build_root_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Paper AI Reader: collect, filter, export, and download papers."
    )
    subparsers = parser.add_subparsers(dest="command")

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch papers and enrich them with metadata into a JSONL file.",
    )
    add_fetch_arguments(fetch_parser)
    fetch_parser.set_defaults(handler=execute_fetch)

    read_parser = subparsers.add_parser(
        "read",
        help="Read fetched papers, score them with AI, and optionally download PDFs.",
    )
    add_read_arguments(read_parser)
    read_parser.set_defaults(handler=execute_read)

    download_parser = subparsers.add_parser(
        "download",
        help="Download PDFs from an existing JSON result file.",
    )
    add_loader_arguments(download_parser)
    download_parser.set_defaults(handler=execute_loader)

    return parser


def run_cli() -> int:
    parser = build_root_parser()
    args = parser.parse_args()

    if not hasattr(args, "handler"):
        parser.print_help()
        return 1

    try:
        return args.handler(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(run_cli())
