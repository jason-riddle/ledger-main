"""Command-line interface for beanout."""

import argparse
import pathlib
import sys

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

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the beanout CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sps":
        try:
            output = beanout.sps.render_sps_file(args.input)
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
