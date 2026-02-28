"""CLI entry point. [FSD-5.1]"""
import argparse
import sys
from pathlib import Path

from proofmark import ConfigError, EncodingError, ProofmarkError
from proofmark.pipeline import run
from proofmark.report import serialize_report


def main() -> None:
    """Entry point. Parses args, runs pipeline, writes report, exits. [FSD-5.1.10]"""
    parser = argparse.ArgumentParser(
        prog="proofmark",
        description="ETL output equivalence comparison tool",
    )
    subparsers = parser.add_subparsers(dest="command")

    compare_parser = subparsers.add_parser("compare", help="Run a comparison")
    compare_parser.add_argument(
        "--config", required=True, type=Path,
        help="Path to YAML config file",
    )
    compare_parser.add_argument(
        "--left", required=True, type=Path,
        help="LHS path (file for CSV, directory for parquet)",
    )
    compare_parser.add_argument(
        "--right", required=True, type=Path,
        help="RHS path (same semantics as --left)",
    )
    compare_parser.add_argument(
        "--output", type=Path, default=None,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    if args.command != "compare":
        parser.print_help()
        sys.exit(2)

    try:
        report = run(args.config, args.left, args.right)
        report_json = serialize_report(report)

        # Write output [FSD-5.1.10 step 4]
        if args.output:
            args.output.write_text(report_json)
        else:
            print(report_json)

        # Exit code [FSD-5.1.6]
        result = report.get("summary", {}).get("result", "FAIL")
        sys.exit(0 if result == "PASS" else 1)

    except (ConfigError, EncodingError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except ProofmarkError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)
