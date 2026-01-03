#!/usr/bin/env python3
"""
Validate JSONL transaction files against the transaction schema.

Usage:
    python schema/validate_jsonl.py schema/examples/sample-transactions.jsonl
    python schema/validate_jsonl.py path/to/file.pdf.jsonl
"""

import argparse
import json
import sys
from pathlib import Path


def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema from file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_jsonl_file(jsonl_path: Path, schema: dict) -> tuple[int, int, list[str]]:
    """
    Validate a JSONL file against the schema.

    Returns:
        tuple: (valid_count, invalid_count, errors)
    """
    try:
        import jsonschema
    except ImportError:
        print(
            "Error: jsonschema library not found. Install with: pip install jsonschema",
            file=sys.stderr,
        )
        sys.exit(1)

    valid_count = 0
    invalid_count = 0
    errors = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                invalid_count += 1
                errors.append(f"Line {line_num}: Invalid JSON - {e}")
                continue

            try:
                jsonschema.validate(obj, schema)
                valid_count += 1
            except jsonschema.ValidationError as e:
                invalid_count += 1
                errors.append(f"Line {line_num}: Schema validation failed - {e.message}")

    return valid_count, invalid_count, errors


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate JSONL transaction files against schema"
    )
    parser.add_argument(
        "jsonl_file",
        type=Path,
        help="Path to the JSONL file to validate",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).parent / "transaction.schema.json",
        help="Path to the schema file (default: transaction.schema.json in same dir)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show all validation errors",
    )

    args = parser.parse_args()

    if not args.jsonl_file.exists():
        print(f"Error: File not found: {args.jsonl_file}", file=sys.stderr)
        return 1

    if not args.schema.exists():
        print(f"Error: Schema file not found: {args.schema}", file=sys.stderr)
        return 1

    print(f"Loading schema from: {args.schema}")
    schema = load_schema(args.schema)

    print(f"Validating: {args.jsonl_file}")
    valid_count, invalid_count, errors = validate_jsonl_file(args.jsonl_file, schema)

    print("\nResults:")
    print(f"  ✓ Valid transactions:   {valid_count}")
    print(f"  ✗ Invalid transactions: {invalid_count}")

    if errors:
        if args.verbose or invalid_count <= 10:
            print("\nValidation Errors:")
            for error in errors:
                print(f"  {error}")
        else:
            print("\nShowing first 10 errors (use --verbose to see all):")
            for error in errors[:10]:
                print(f"  {error}")

    return 0 if invalid_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
