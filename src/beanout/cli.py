"""Command-line interface for beanout."""

import argparse
import pathlib
import sys

import beanout.clover_leaf
import beanout.sheer_value
import beanout.sps


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="beanout",
        description="Generate Beancount output from statement text.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sps_parser = subparsers.add_parser(
        "sps",
        help="Parse SPS .pdf.txt files.",
    )
    sps_parser.add_argument(
        "--input",
        required=True,
        help="Path to the SPS .pdf.txt file.",
    )
    sps_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    sps_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    clover_leaf_parser = subparsers.add_parser(
        "clover-leaf",
        help="Parse CloverLeaf .pdf.txt files.",
    )
    clover_leaf_parser.add_argument(
        "--input",
        required=True,
        help="Path to the CloverLeaf .pdf.txt file.",
    )
    clover_leaf_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    clover_leaf_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    sheer_value_parser = subparsers.add_parser(
        "sheer-value",
        help="Parse Sheer Value .pdf.txt files.",
    )
    sheer_value_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Sheer Value .pdf.txt file.",
    )
    sheer_value_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    sheer_value_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the beanout CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sps":
        try:
            if args.jsonl:
                output = beanout.sps.render_sps_file_to_jsonl(args.input)
            else:
                output = beanout.sps.render_sps_file(args.input)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        if args.output == "-":
            sys.stdout.write(output)
        else:
            pathlib.Path(args.output).write_text(output, encoding="utf-8")

    if args.command == "clover-leaf":
        try:
            if args.jsonl:
                output = beanout.clover_leaf.render_clover_leaf_file_to_jsonl(args.input)
            else:
                output = beanout.clover_leaf.render_clover_leaf_file(args.input)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        if args.output == "-":
            sys.stdout.write(output)
        else:
            pathlib.Path(args.output).write_text(output, encoding="utf-8")

    if args.command == "sheer-value":
        try:
            if args.jsonl:
                output = beanout.sheer_value.render_sheer_value_file_to_jsonl(args.input)
            else:
                output = beanout.sheer_value.render_sheer_value_file(args.input)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        if args.output == "-":
            sys.stdout.write(output)
        else:
            pathlib.Path(args.output).write_text(output, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
