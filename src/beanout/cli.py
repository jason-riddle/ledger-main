"""Command-line interface for beanout."""

import argparse
import pathlib
import sys

import beanout.clover_leaf
import beanout.fidelity
import beanout.ally_bank
import beanout.chase
import beanout.schwab
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

    clover_leaf_csv_parser = subparsers.add_parser(
        "clover-leaf-csv",
        help="Parse CloverLeaf .csv files.",
    )
    clover_leaf_csv_parser.add_argument(
        "--input",
        required=True,
        help="Path to the CloverLeaf .csv file.",
    )
    clover_leaf_csv_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    clover_leaf_csv_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    clover_leaf_json_parser = subparsers.add_parser(
        "clover-leaf-json",
        help="Parse CloverLeaf .json files.",
    )
    clover_leaf_json_parser.add_argument(
        "--input",
        required=True,
        help="Path to the CloverLeaf .json file.",
    )
    clover_leaf_json_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    clover_leaf_json_parser.add_argument(
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

    fidelity_parser = subparsers.add_parser(
        "fidelity",
        help="Parse Fidelity .csv files.",
    )
    fidelity_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Fidelity .csv file.",
    )
    fidelity_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    fidelity_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    ally_bank_csv_parser = subparsers.add_parser(
        "ally-bank-csv",
        help="Parse Ally Bank .csv files.",
    )
    ally_bank_csv_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Ally Bank .csv file.",
    )
    ally_bank_csv_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    ally_bank_csv_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    ally_bank_qfx_parser = subparsers.add_parser(
        "ally-bank-qfx",
        help="Parse Ally Bank .qfx files.",
    )
    ally_bank_qfx_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Ally Bank .qfx file.",
    )
    ally_bank_qfx_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    ally_bank_qfx_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    chase_csv_parser = subparsers.add_parser(
        "chase-csv",
        help="Parse Chase .csv files.",
    )
    chase_csv_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Chase .csv file.",
    )
    chase_csv_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    chase_csv_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    chase_qfx_parser = subparsers.add_parser(
        "chase-qfx",
        help="Parse Chase .qfx files.",
    )
    chase_qfx_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Chase .qfx file.",
    )
    chase_qfx_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    chase_qfx_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    schwab_parser = subparsers.add_parser(
        "schwab",
        help="Parse Schwab .json files.",
    )
    schwab_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Schwab .json file.",
    )
    schwab_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    schwab_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    schwab_xml_parser = subparsers.add_parser(
        "schwab-xml",
        help="Parse Schwab .xml files.",
    )
    schwab_xml_parser.add_argument(
        "--input",
        required=True,
        help="Path to the Schwab .xml file.",
    )
    schwab_xml_parser.add_argument(
        "--output",
        default="-",
        help="Output path or '-' for stdout (default).",
    )
    schwab_xml_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output in JSONL format instead of Beancount format.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the beanout CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Map command to render functions (bean and jsonl)
    render_funcs = {
        "sps": (
            beanout.sps.render_sps_file,
            beanout.sps.render_sps_file_to_jsonl,
        ),
        "clover-leaf": (
            beanout.clover_leaf.render_clover_leaf_file,
            beanout.clover_leaf.render_clover_leaf_file_to_jsonl,
        ),
        "clover-leaf-csv": (
            beanout.clover_leaf.render_clover_leaf_csv_file,
            beanout.clover_leaf.render_clover_leaf_csv_file_to_jsonl,
        ),
        "clover-leaf-json": (
            beanout.clover_leaf.render_clover_leaf_json_file,
            beanout.clover_leaf.render_clover_leaf_json_file_to_jsonl,
        ),
        "sheer-value": (
            beanout.sheer_value.render_sheer_value_file,
            beanout.sheer_value.render_sheer_value_file_to_jsonl,
        ),
        "fidelity": (
            beanout.fidelity.render_fidelity_csv_file,
            beanout.fidelity.render_fidelity_csv_file_to_jsonl,
        ),
        "ally-bank-csv": (
            beanout.ally_bank.render_ally_bank_csv_file,
            beanout.ally_bank.render_ally_bank_csv_file_to_jsonl,
        ),
        "ally-bank-qfx": (
            beanout.ally_bank.render_ally_bank_qfx_file,
            beanout.ally_bank.render_ally_bank_qfx_file_to_jsonl,
        ),
        "chase-csv": (
            beanout.chase.render_chase_csv_file,
            beanout.chase.render_chase_csv_file_to_jsonl,
        ),
        "chase-qfx": (
            beanout.chase.render_chase_qfx_file,
            beanout.chase.render_chase_qfx_file_to_jsonl,
        ),
        "schwab": (
            beanout.schwab.render_schwab_json_file,
            beanout.schwab.render_schwab_json_file_to_jsonl,
        ),
        "schwab-xml": (
            beanout.schwab.render_schwab_xml_file,
            beanout.schwab.render_schwab_xml_file_to_jsonl,
        ),
    }

    if args.command in render_funcs:
        render_func = render_funcs[args.command][1 if args.jsonl else 0]
        try:
            output = render_func(args.input)
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
