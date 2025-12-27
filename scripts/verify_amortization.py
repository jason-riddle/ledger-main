#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "beancount>=3.0.0",
# ]
# ///

"""
Verify Mortgage Amortization Calculations

This script verifies that mortgage payment transactions in the Beancount ledger
match the expected amortization calculations using standard loan formulas:
- Monthly interest = (Annual Rate / 12) × Remaining Principal
- Principal payment = Total Payment - Interest
- New Balance = Old Balance - Principal Payment

Usage:
    ./scripts/verify_amortization.py
    uv run scripts/verify_amortization.py

Exit codes:
    0 - All amortization calculations verified successfully
    1 - Discrepancies found or errors occurred
"""

import collections
import datetime
import decimal
import pathlib
import sys
from typing import TypedDict

# Add utils to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from utils import amortization

# Beancount imports
try:
    from beancount import loader
    from beancount.core import data
except ImportError:
    print("Error: beancount library not found. Install with: pip install beancount")
    sys.exit(1)


class MortgageConfig(TypedDict):
    name: str
    original_principal: float
    annual_rate: float
    term_years: int
    start_date: str
    expected_payment: float


# Mortgage configurations
MORTGAGE_CONFIGS: dict[str, MortgageConfig] = {
    "2943-Butterfly-Palm": {
        "name": "2943 Butterfly Palm Mortgage",
        "original_principal": 102500,
        "annual_rate": 8.625,
        "term_years": 30,
        "start_date": "2022-11-09",  # First payment date
        "expected_payment": 797.23,  # P+I only, excluding escrow
    },
}


class PaymentInfo(TypedDict):
    date: datetime.date
    narration: str
    interest: decimal.Decimal | None
    principal: decimal.Decimal | None
    escrow: decimal.Decimal | None
    total: decimal.Decimal | None


def extract_mortgage_payments(entries):
    """
    Extract mortgage payment transactions from ledger entries.

    Returns a dictionary mapping property names to lists of payment details.
    """

    class VerifiedPaymentInfo(TypedDict):
        date: datetime.date
        narration: str
        interest: decimal.Decimal
        principal: decimal.Decimal
        escrow: decimal.Decimal | None
        total: decimal.Decimal | None

    mortgage_payments: dict[str, list[VerifiedPaymentInfo]] = collections.defaultdict(
        list
    )
    for entry in entries:
        if not isinstance(entry, data.Transaction):
            continue

        # Look for mortgage payment transactions
        if "mortgage payment" not in entry.narration.lower():
            continue

        # Extract payment details from postings
        payment_info: PaymentInfo = {
            "date": entry.date,
            "narration": entry.narration,
            "interest": None,
            "principal": None,
            "escrow": None,
            "total": None,
        }
        property_name: str | None = None
        for posting in entry.postings:
            account = posting.account
            amt = posting.units.number

            if "Mortgage-Interest" in account:
                payment_info["interest"] = abs(amt)
                # Extract property name
                parts = account.split(":")
                if len(parts) >= 3:
                    property_name = parts[2]
            elif "Mortgages" in account and "Liabilities" in account:
                # Principal payment (positive posting to liability = reduction)
                payment_info["principal"] = abs(amt)
                # Extract property name if not already found
                parts = account.split(":")
                if len(parts) >= 2:
                    property_name = parts[2] if len(parts) >= 3 else parts[1]
            elif "Escrow" in account:
                payment_info["escrow"] = abs(amt)
            elif "Checking" in account or "Cash" in account:
                payment_info["total"] = abs(amt)

        if (
            property_name
            and payment_info["interest"] is not None
            and payment_info["principal"] is not None
        ):
            completed: VerifiedPaymentInfo = {
                "date": payment_info["date"],
                "narration": payment_info["narration"],
                "interest": payment_info["interest"],
                "principal": payment_info["principal"],
                "escrow": payment_info["escrow"],
                "total": payment_info["total"],
            }
            mortgage_payments[property_name].append(completed)

    return mortgage_payments


def get_balance_at_date(entries, account_pattern, target_date):
    """
    Calculate account balance at a specific date by summing postings.

    Returns balance as Decimal.
    """
    balance = decimal.Decimal("0")

    for entry in entries:
        if not isinstance(entry, data.Transaction):
            continue

        if entry.date > target_date:
            break

        for posting in entry.postings:
            if account_pattern in posting.account:
                balance += decimal.Decimal(str(posting.units.number))

    return balance


def verify_mortgage_amortization(ledger_path: str = "ledger/main.bean"):
    """
    Verify mortgage amortization calculations in the ledger.

    Returns True if all calculations are correct, False otherwise.
    """
    print("=" * 80)
    print("MORTGAGE AMORTIZATION VERIFICATION")
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

    # Extract mortgage payments
    print("Extracting mortgage payment transactions...")
    mortgage_payments = extract_mortgage_payments(entries)
    print(f"Found {len(mortgage_payments)} mortgages with payments\n")

    # Verify each mortgage
    all_correct = True
    total_checked = 0
    total_discrepancies = 0

    for property_name, payments in sorted(mortgage_payments.items()):
        config = MORTGAGE_CONFIGS.get(property_name)

        if not config:
            print(f"⚠️  Mortgage not configured: {property_name}")
            print(f"   Found {len(payments)} payments but no configuration")
            print()
            continue

        print(f"📋 {config['name']}")
        print(f"   Original Principal: ${config['original_principal']:,.2f}")
        print(f"   Annual Rate: {config['annual_rate']}%")
        print(f"   Term: {config['term_years']} years")
        print(f"   Expected P+I Payment: ${config['expected_payment']}")
        print(f"   Payments Found: {len(payments)}")
        print()

        # Sort payments by date
        payments.sort(key=lambda p: p["date"])

        # Track running balance
        mortgage_account = f"Liabilities:Mortgages:{property_name}"

        # Check each payment
        discrepancies = []
        prev_date = None

        for i, payment in enumerate(payments):
            # Get balance before this payment
            # We need to look at balance just before this payment
            if prev_date:
                balance_before = get_balance_at_date(
                    entries, mortgage_account, prev_date
                )
            else:
                # For first payment, get initial balance
                balance_before = get_balance_at_date(
                    entries, mortgage_account, payment["date"].replace(day=1)
                )

            balance_before = abs(balance_before)  # Liabilities are negative

            # Calculate expected values
            expected_interest = amortization.calculate_interest_payment(
                float(balance_before), config["annual_rate"]
            )
            expected_principal = amortization.calculate_principal_payment(
                config["expected_payment"], float(expected_interest)
            )

            # Compare with actual
            actual_interest = decimal.Decimal(str(payment["interest"]))
            actual_principal = decimal.Decimal(str(payment["principal"]))

            interest_diff = abs(actual_interest - expected_interest)
            principal_diff = abs(actual_principal - expected_principal)

            # Allow small rounding differences (5 cents for each)
            if interest_diff > decimal.Decimal(
                "0.05"
            ) or principal_diff > decimal.Decimal("0.05"):
                discrepancies.append(
                    {
                        "date": payment["date"],
                        "balance_before": balance_before,
                        "expected_interest": expected_interest,
                        "actual_interest": actual_interest,
                        "interest_diff": interest_diff,
                        "expected_principal": expected_principal,
                        "actual_principal": actual_principal,
                        "principal_diff": principal_diff,
                    }
                )

            prev_date = payment["date"]

        if discrepancies:
            print(f"   ❌ Found {len(discrepancies)} discrepancies:")
            for disc in discrepancies[:5]:  # Show first 5
                print(f"      {disc['date']}:")
                print(f"         Balance: ${disc['balance_before']:,.2f}")
                print(
                    "         Interest: Expected $"
                    f"{disc['expected_interest']}, Actual $"
                    f"{disc['actual_interest']}, Diff $"
                    f"{disc['interest_diff']}"
                )
                print(
                    "         Principal: Expected $"
                    f"{disc['expected_principal']}, Actual $"
                    f"{disc['actual_principal']}, Diff $"
                    f"{disc['principal_diff']}"
                )
            if len(discrepancies) > 5:
                print(f"      ... and {len(discrepancies) - 5} more")
            all_correct = False
            total_discrepancies += len(discrepancies)
        else:
            print(f"   ✓ All {len(payments)} payments verified correctly")

        total_checked += len(payments)
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total mortgages checked: {len(mortgage_payments)}")
    print(f"Total payments checked: {total_checked}")

    if all_correct:
        print("\n✅ SUCCESS: All amortization calculations verified!")
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
        success = verify_mortgage_amortization(str(ledger_path))
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
