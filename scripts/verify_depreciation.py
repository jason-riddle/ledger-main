#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "beancount>=3.0.0",
# ]
# ///

"""
Verify Depreciation Calculations

This script verifies that depreciation transactions in the Beancount ledger
match the expected IRS depreciation calculations using:
- 27.5-year straight-line for residential rental buildings and improvements
- 30-year straight-line for loan costs
- Mid-month convention for first/last year

Usage:
    ./scripts/verify_depreciation.py
    uv run scripts/verify_depreciation.py

Exit codes:
    0 - All depreciation calculations verified successfully
    1 - Discrepancies found or errors occurred
"""

import collections
import decimal
import pathlib
import sys

# Add utils to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from utils import depreciation

# Beancount imports
try:
    from beancount import loader
    from beancount.core import data
except ImportError:
    print("Error: beancount library not found. Install with: pip install beancount")
    sys.exit(1)


# Asset configurations from _notes/_depreciation.md
ASSET_CONFIGS = {
    "2943-Butterfly-Palm:Building:2023-01-01-Building": {
        "name": "2943 Butterfly Palm Building",
        "cost_basis": 164791,
        "recovery_years": 27.5,
        "month_placed": 1,
        "year_placed": 2023,
    },
    "2943-Butterfly-Palm:Improvements:2023-01-01-Back-Door": {
        "name": "2943 Butterfly Palm Back Door",
        "cost_basis": 600,
        "recovery_years": 27.5,
        "month_placed": 1,
        "year_placed": 2023,
    },
    "2943-Butterfly-Palm:Loan-Costs:2023-01-01-Loan-Costs-2023-SPS-Mortgage": {
        "name": "2943 Butterfly Palm Loan Costs",
        "cost_basis": 2389,
        "recovery_years": 30,
        "month_placed": 1,
        "year_placed": 2023,
    },
    "2943-Butterfly-Palm:Improvements:2023-02-17-Water-Heater": {
        "name": "2943 Butterfly Palm Water Heater (2023-02-17)",
        "cost_basis": 2895,
        "recovery_years": 27.5,
        "month_placed": 2,
        "year_placed": 2023,
    },
    "2943-Butterfly-Palm:Improvements:2024-05-08-Water-Heater": {
        "name": "2943 Butterfly Palm Water Heater (2024-05-08)",
        "cost_basis": 2800.75,
        "recovery_years": 27.5,
        "month_placed": 5,
        "year_placed": 2024,
    },
    "206-Hoover-Ave:Building:2023-05-26-Building": {
        "name": "206 Hoover Ave Building",
        "cost_basis": 73358,
        "recovery_years": 27.5,
        "month_placed": 5,
        "year_placed": 2023,
    },
    "206-Hoover-Ave:Improvements:2023-11-17-Improvements": {
        "name": "206 Hoover Ave Improvements",
        "cost_basis": 30302,
        "recovery_years": 27.5,
        "month_placed": 11,
        "year_placed": 2023,
    },
}


def find_asset_config(account_name: str):
    """Find asset configuration matching the account name."""
    for key, config in ASSET_CONFIGS.items():
        if key in account_name:
            return config
    return None


def extract_depreciation_transactions(entries):
    """
    Extract depreciation transactions from ledger entries.

    Returns a dictionary mapping asset accounts to lists of depreciation
    postings.
    """
    depreciation_txns = collections.defaultdict(list)

    for entry in entries:
        if not isinstance(entry, data.Transaction):
            continue

        # Look for depreciation transactions
        if "depreciation" not in entry.narration.lower():
            continue

        # Find accumulated depreciation postings (negative amounts)
        for posting in entry.postings:
            if "Accumulated-Depreciation" in posting.account:
                # Extract the asset identifier from account path
                # e.g., "Assets:Accumulated-Depreciation:2943-Butterfly-Palm:"
                # "Building:2023-01-01-Building"
                parts = posting.account.split(":")
                if len(parts) >= 4:
                    # Get property and asset parts
                    asset_key = ":".join(
                        parts[2:]
                    )  # "2943-Butterfly-Palm:Building:2023-01-01-Building"

                    depreciation_txns[asset_key].append(
                        {
                            "date": entry.date,
                            "amount": abs(posting.units.number),
                            "account": posting.account,
                            "narration": entry.narration,
                        }
                    )

    return depreciation_txns


def verify_depreciation(ledger_path: str = "ledger/main.bean"):
    """
    Verify depreciation calculations in the ledger.

    Returns True if all calculations are correct, False otherwise.
    """
    print("=" * 80)
    print("DEPRECIATION VERIFICATION")
    print("=" * 80)
    print()

    # Load ledger
    ledger_abs_path = pathlib.Path(ledger_path).absolute()
    if not ledger_abs_path.exists():
        print(f"Error: Ledger file not found: {ledger_abs_path}")
        return False

    print(f"Loading ledger: {ledger_abs_path}")
    entries, errors, options = loader.load_file(str(ledger_abs_path))
    del options  # Unused.

    if errors:
        print(f"\nWarning: {len(errors)} errors found in ledger:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
        print()

    # Extract depreciation transactions
    print("Extracting depreciation transactions...")
    depreciation_txns = extract_depreciation_transactions(entries)
    print(f"Found {len(depreciation_txns)} assets with depreciation\n")

    # Verify each asset
    all_correct = True
    total_checked = 0
    total_discrepancies = 0
    monthly_tolerance = decimal.Decimal("0.03")
    total_tolerance = decimal.Decimal("0.50")

    for asset_key, txns in sorted(depreciation_txns.items()):
        config = find_asset_config(asset_key)

        if not config:
            print(f"⚠️  Asset not configured: {asset_key}")
            print(f"   Found {len(txns)} transactions but no configuration")
            print()
            all_correct = False
            continue

        print(f"📋 {config['name']}")
        print(f"   Cost Basis: ${config['cost_basis']:,.2f}")
        print(f"   Recovery: {config['recovery_years']} years")
        placed_date = f"{config['year_placed']}-{config['month_placed']:02d}"
        print(f"   Placed: {placed_date}")

        # Calculate expected monthly amount
        expected_monthly = depreciation.calculate_monthly_depreciation(
            config["cost_basis"], config["recovery_years"]
        )

        print(f"   Expected Monthly: ${expected_monthly}")
        print(f"   Transactions: {len(txns)}")

        # Check each transaction
        discrepancies = []
        txns_by_year = collections.defaultdict(list)
        for txn in txns:
            txns_by_year[txn["date"].year].append(txn)

        for year, year_txns in sorted(txns_by_year.items()):
            total_actual = sum(decimal.Decimal(str(txn["amount"])) for txn in year_txns)
            if year == config["year_placed"]:
                expected_total = depreciation.calculate_first_year_depreciation(
                    config["cost_basis"],
                    config["recovery_years"],
                    config["month_placed"],
                )
                check_monthly = False
            else:
                if len(year_txns) < 12:
                    expected_total = (
                        expected_monthly * decimal.Decimal(len(year_txns))
                    ).quantize(decimal.Decimal("0.01"))
                else:
                    expected_total = depreciation.calculate_annual_depreciation(
                        config["cost_basis"],
                        config["recovery_years"],
                    )
                check_monthly = True

            total_diff = abs(total_actual - expected_total)
            if total_diff > total_tolerance:
                discrepancies.append(
                    {
                        "kind": "year-total",
                        "year": year,
                        "expected": expected_total,
                        "actual": total_actual,
                        "difference": total_diff,
                    }
                )

            if check_monthly:
                for txn in year_txns:
                    actual = decimal.Decimal(str(txn["amount"]))
                    diff = abs(actual - expected_monthly)
                    if diff > monthly_tolerance:
                        discrepancies.append(
                            {
                                "kind": "monthly",
                                "date": txn["date"],
                                "expected": expected_monthly,
                                "actual": actual,
                                "difference": diff,
                            }
                        )

        if discrepancies:
            print(f"   ❌ Found {len(discrepancies)} discrepancies:")
            for disc in discrepancies[:3]:  # Show first 3
                if disc["kind"] == "year-total":
                    print(
                        f"      {disc['year']}: Expected total "
                        f"${disc['expected']}, Got ${disc['actual']}, "
                        f"Diff ${disc['difference']}"
                    )
                else:
                    print(
                        f"      {disc['date']}: Expected ${disc['expected']}, "
                        f"Got ${disc['actual']}, Diff ${disc['difference']}"
                    )
            if len(discrepancies) > 3:
                print(f"      ... and {len(discrepancies) - 3} more")
            all_correct = False
            total_discrepancies += len(discrepancies)
        else:
            print(f"   ✓ All {len(txns)} transactions correct")

        total_checked += len(txns)
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total assets checked: {len(depreciation_txns)}")
    print(f"Total transactions checked: {total_checked}")

    if all_correct:
        print("\n✅ SUCCESS: All depreciation calculations verified!")
        return True
    else:
        print(f"\n❌ FAILED: Found {total_discrepancies} discrepancies")
        return False


def main():
    """Main entry point."""
    # Determine ledger path
    script_dir = pathlib.Path(__file__).parent
    repo_root = script_dir.parent
    ledger_path = repo_root / "ledger" / "main.bean"

    try:
        success = verify_depreciation(str(ledger_path))
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
