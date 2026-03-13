"""CLI entry point. [FSD-5.1]"""
import argparse
import logging
import sys
from pathlib import Path


def main() -> None:
    """Entry point. Parses args, dispatches to serve subcommand. [FSD-5.1.10]"""
    parser = argparse.ArgumentParser(
        prog="proofmark",
        description="ETL output equivalence comparison tool",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser(
        "serve", help="Start the comparison queue runner",
    )
    serve_parser.add_argument(
        "--settings", type=Path, default=None,
        help="Path to YAML settings file (optional — sensible defaults built in)",
    )
    serve_parser.add_argument(
        "--init-db", action="store_true",
        help="Create the queue table if it doesn't exist",
    )

    args = parser.parse_args()

    if args.command == "serve":
        try:
            from proofmark.app_config import load_app_config
            from proofmark.queue import serve
        except ImportError:
            print(
                "Error: psycopg2 is required for the queue runner. "
                "Install with: pip install proofmark[queue]",
                file=sys.stderr,
            )
            sys.exit(2)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )
        config = load_app_config(args.settings)
        serve(config=config, do_init=args.init_db)
        return

    parser.print_help()
    sys.exit(2)
