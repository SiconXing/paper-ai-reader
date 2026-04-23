import dotenv

dotenv.load_dotenv()

import argparse

from loader.cli import add_loader_arguments, execute_loader
from reader.cli import add_reader_arguments, execute_reader


def build_root_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Paper AI Reader: collect, filter, export, and download papers."
    )
    subparsers = parser.add_subparsers(dest="command")

    collect_parser = subparsers.add_parser(
        "collect",
        help="Fetch papers, enrich abstracts, rank with AI, and optionally download PDFs.",
    )
    add_reader_arguments(collect_parser)
    collect_parser.set_defaults(handler=execute_reader)

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
