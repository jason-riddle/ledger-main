#!/usr/bin/env python3
"""
Convert JSONL transaction file to Beancount format.

This demonstrates the final step of the pipeline:
  .pdf → .pdf.txt → .pdf.jsonl → .pdf.bean (this script)

Usage:
    python schema/jsonl_to_bean.py input.jsonl output.bean
    python schema/jsonl_to_bean.py input.jsonl  # outputs to stdout
"""

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path


def format_amount(amount: float | Decimal) -> str:
    """Format amount with 2 decimal places, no trailing zeros."""
    if isinstance(amount, float):
        amount = Decimal(str(amount))

    if amount == 0:
        return "0"

    # Format with 2 decimal places
    formatted = f"{abs(amount):.2f}"
    # Remove trailing zeros after decimal point but keep at least .X
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")

    return f"-{formatted}" if amount < 0 else formatted


def format_posting(account: str, amount: float, currency: str = "USD") -> str:
    """Format a posting line with proper alignment."""
    amount_str = format_amount(amount)
    prefix = f"  {account}"
    # Align amount at column 69
    amount_end_col = 69
    spaces = amount_end_col - len(prefix) - len(amount_str)
    if spaces < 1:
        spaces = 1
    return f"{prefix}{' ' * spaces}{amount_str} {currency}"


def convert_transaction_to_bean(txn: dict) -> list[str]:
    """Convert a single transaction object to Beancount format."""
    lines = []

    # Build header: date flag "payee" "description" #tags
    date = txn["date"]
    payee = txn["payee_payer"]
    description = txn["description"]
    tags = txn.get("tags", [])

    header = f'{date} * "{payee}" "{description}"'
    if tags:
        tags_str = " ".join(f"#{tag}" for tag in sorted(tags))
        header = f"{header} {tags_str}"

    lines.append(header)

    # Add postings (sorted by amount: negative first, then positive)
    entries = sorted(txn["entries"], key=lambda e: e["amount_usd"])
    for entry in entries:
        lines.append(format_posting(entry["account"], entry["amount_usd"]))

    return lines


def convert_jsonl_to_bean(jsonl_path: Path) -> tuple[str, list[str]]:
    """
    Convert a JSONL file to Beancount format.

    Returns:
        tuple: (beancount_text, errors)
    """
    lines: list[str] = []
    errors: list[str] = []
    transaction_count = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: Invalid JSON - {e}")
                continue

            if not obj.get("ok"):
                error_msg = obj.get("error", "Unknown error")
                errors.append(
                    f"Line {line_num}: Skipped failed transaction - {error_msg}"
                )
                continue

            transaction = obj.get("transaction")
            if not transaction:
                errors.append(f"Line {line_num}: Missing transaction object")
                continue

            # Convert transaction to Beancount format
            try:
                txn_lines = convert_transaction_to_bean(transaction)
                if lines:
                    lines.append("")  # Blank line between transactions
                lines.extend(txn_lines)
                transaction_count += 1
            except Exception as e:
                errors.append(f"Line {line_num}: Conversion error - {e}")

    beancount_text = "\n".join(lines)
    if lines:
        beancount_text += "\n"  # Final newline

    if transaction_count > 0:
        errors.insert(0, f"Successfully converted {transaction_count} transaction(s)")

    return beancount_text, errors


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert JSONL transactions to Beancount format"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input JSONL file",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output .bean file (default: stdout)",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    beancount_text, messages = convert_jsonl_to_bean(args.input)

    # Print messages to stderr
    for msg in messages:
        print(msg, file=sys.stderr)

    # Output Beancount text
    if args.output:
        args.output.write_text(beancount_text, encoding="utf-8")
        print(f"Wrote output to: {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(beancount_text)

    # Return non-zero if there were any non-success messages
    error_count = sum(1 for msg in messages if "Error" in msg or "error" in msg)
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
