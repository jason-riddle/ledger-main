#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = [
# ]
# ///

"""
Generate Beancount depreciation postings (straight-line, mid-month convention).

Supports:
- Yearly output (YYYY) or date-range output (YYYY-MM to YYYY-MM)
- First-year annual or monthly output
- Optional end-date truncation
- Optional balance assertion
"""

import argparse
import calendar
import dataclasses
import datetime
import decimal
from typing import Iterable

from utils import depreciation


@dataclasses.dataclass(frozen=True)
class YearMonth:
    """Container for a year and month pair."""

    year: int
    month: int

    def to_date(self, day: int) -> datetime.date:
        """Return a date within the month, validating the day."""
        last_day = calendar.monthrange(self.year, self.month)[1]
        if day < 1 or day > last_day:
            raise ValueError(
                f"Invalid day {day} for {self.year}-{self.month:02d} "
                f"(last day {last_day})."
            )
        return datetime.date(self.year, self.month, day)


@dataclasses.dataclass(frozen=True)
class MonthEntry:
    """Container for a month entry with weight."""

    year: int
    month: int
    weight: decimal.Decimal

    def year_month(self) -> YearMonth:
        """Return the YearMonth for this entry."""
        return YearMonth(self.year, self.month)


def parse_year_month(value: str) -> YearMonth:
    """Parse a YYYY-MM string into a YearMonth."""
    try:
        parts = value.split("-")
        if len(parts) != 2:
            raise ValueError
        year = int(parts[0])
        month = int(parts[1])
        if month < 1 or month > 12:
            raise ValueError
        return YearMonth(year=year, month=month)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Expected YYYY-MM with a valid month (01-12)."
        ) from exc


def parse_date(value: str) -> datetime.date:
    """Parse an ISO YYYY-MM-DD date string."""
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected YYYY-MM-DD date.") from exc


def parse_decimal(value: str) -> decimal.Decimal:
    """Parse a decimal string into a Decimal."""
    try:
        return decimal.Decimal(value)
    except decimal.InvalidOperation as exc:
        # pragma: no cover - argparse error path
        raise argparse.ArgumentTypeError("Expected a decimal number.") from exc


def month_index_from_start(start: YearMonth, target: YearMonth) -> int:
    """Return 1-based month index from start to target."""
    start_total = start.year * 12 + (start.month - 1)
    target_total = target.year * 12 + (target.month - 1)
    return (target_total - start_total) + 1


def iter_months(start: YearMonth, end: YearMonth) -> Iterable[YearMonth]:
    """Yield YearMonth values from start through end inclusive."""
    current = YearMonth(start.year, start.month)
    while (current.year, current.month) <= (end.year, end.month):
        yield current
        if current.month == 12:
            current = YearMonth(current.year + 1, 1)
        else:
            current = YearMonth(current.year, current.month + 1)


def quantize_to_increment(
    value: decimal.Decimal, increment: decimal.Decimal
) -> decimal.Decimal:
    """Round a value to the nearest increment."""
    if increment <= 0:
        raise ValueError("Rounding increment must be positive.")
    return (value / increment).quantize(
        decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP
    ) * increment


def cents_int(value: decimal.Decimal) -> int:
    """Convert a Decimal dollar amount to integer cents."""
    return int(
        (value * decimal.Decimal("100")).to_integral_value(
            rounding=decimal.ROUND_HALF_UP
        )
    )


def normalize_tags(raw_tags: list[str]) -> list[str]:
    """Normalize comma-separated tag strings into a flat list."""
    tags: list[str] = []
    for raw in raw_tags:
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        tags.extend(parts)
    return tags


def format_amount(value: decimal.Decimal, currency: str) -> str:
    """Format a decimal currency amount with two decimals."""
    return f"{value:.2f} {currency}"


def build_posting_lines(
    accum_account: str,
    expense_account: str,
    amount: decimal.Decimal,
    currency: str,
) -> list[str]:
    """Build aligned posting lines for a depreciation transaction."""
    accounts = [accum_account, expense_account]
    max_len = max(len(account) for account in accounts)
    padding = max_len + 2

    lines = []
    for account, posting_amount in (
        (accum_account, -amount),
        (expense_account, amount),
    ):
        spaces = " " * max(2, padding - len(account))
        line = f"   {account}{spaces}{format_amount(posting_amount, currency)}"
        lines.append(line)
    return lines


def build_transaction(
    txn_date: datetime.date,
    narration: str,
    tags: list[str],
    posting_lines: list[str],
) -> list[str]:
    """Build a full transaction block with postings."""
    tag_str = " ".join(f"#{tag}" for tag in tags) if tags else ""
    header = f'{txn_date.isoformat()} * "{narration}"'
    if tag_str:
        header = f"{header} {tag_str}"
    return [header, *posting_lines, ""]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Beancount depreciation postings."
    )
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--placed-in-service", type=parse_date, required=True)
    parser.add_argument("--cost-basis", type=float, required=True)
    parser.add_argument("--recovery-years", type=float, required=True)

    parser.add_argument("--accum-account", required=True)
    parser.add_argument("--expense-account", required=True)
    parser.add_argument("--currency", default="USD")

    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--entry-label", default="Depreciation")
    parser.add_argument("--narration", help="Override narration text.")

    parser.add_argument("--year", type=int)
    parser.add_argument("--from-date", type=parse_year_month)
    parser.add_argument("--to-date", type=parse_year_month)
    parser.add_argument("--end-date", type=parse_date)

    parser.add_argument(
        "--first-year-mode",
        choices=("annual", "monthly"),
        default="annual",
        help="Output mode for the placed-in-service year.",
    )
    parser.add_argument("--monthly-day", type=int, default=15)
    parser.add_argument("--annual-date", type=parse_date)
    parser.add_argument(
        "--annual-rounding", type=parse_decimal, default=decimal.Decimal("1.00")
    )

    parser.add_argument("--include-balance", action="store_true")
    parser.add_argument("--balance-date", type=parse_date)
    parser.add_argument(
        "--starting-accumulated",
        type=parse_decimal,
        default=decimal.Decimal("0.00"),
        help="Starting accumulated depreciation as a positive number.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the depreciation generator."""
    args = parse_args()

    if args.recovery_years <= 0:
        raise SystemExit("recovery-years must be positive.")

    if args.year and (args.from_date or args.to_date):
        raise SystemExit("Use --year or --from-date/--to-date, not both.")
    if (args.from_date is None) ^ (args.to_date is None):
        raise SystemExit("--from-date and --to-date must be provided together.")

    if args.year is None and args.from_date is None:
        raise SystemExit("Provide either --year or --from-date/--to-date.")

    if args.year:
        start_range = YearMonth(args.year, 1)
        end_range = YearMonth(args.year, 12)
    else:
        start_range = args.from_date
        end_range = args.to_date

    if args.end_date:
        end_month = YearMonth(args.end_date.year, args.end_date.month)
        if (end_month.year, end_month.month) < (
            start_range.year,
            start_range.month,
        ):
            raise SystemExit("end-date is before the selected range.")
        if (end_month.year, end_month.month) < (
            end_range.year,
            end_range.month,
        ):
            end_range = end_month

    placed_date: datetime.date = args.placed_in_service
    placed_month = YearMonth(placed_date.year, placed_date.month)

    total_months_raw = decimal.Decimal(str(args.recovery_years)) * decimal.Decimal("12")
    total_months = int(total_months_raw)
    if decimal.Decimal(str(total_months)) != total_months_raw:
        raise SystemExit("recovery-years must convert to a whole number of months.")

    if args.first_year_mode == "annual":
        if args.year is None:
            raise SystemExit("first-year-mode annual requires --year.")
        if args.end_date:
            raise SystemExit("annual mode does not support --end-date.")

    monthly = depreciation.calculate_monthly_depreciation(
        args.cost_basis, args.recovery_years
    )
    annual = depreciation.calculate_annual_depreciation(
        args.cost_basis, args.recovery_years
    )

    months_by_year: dict[int, list[MonthEntry]] = {}
    for ym in iter_months(start_range, end_range):
        idx = month_index_from_start(placed_month, ym)
        if idx < 1 or idx > total_months:
            continue
        if idx == 1 or idx == total_months:
            weight = decimal.Decimal("0.5")
        else:
            weight = decimal.Decimal("1.0")
        months_by_year.setdefault(ym.year, []).append(
            MonthEntry(year=ym.year, month=ym.month, weight=weight)
        )

    if not months_by_year:
        raise SystemExit("No depreciation months within the requested range.")

    tags = normalize_tags(args.tag)
    if "depreciation" not in tags:
        tags.insert(0, "depreciation")

    output_lines: list[str] = []
    total_depreciation = decimal.Decimal("0.00")

    for year in sorted(months_by_year.keys()):
        entries = months_by_year[year]
        if args.first_year_mode == "annual" and year == placed_month.year:
            amount = depreciation.calculate_first_year_depreciation(
                args.cost_basis, args.recovery_years, placed_month.month
            )
            amount = quantize_to_increment(amount, args.annual_rounding)
            narration = (
                args.narration
                if args.narration
                else f"Annual {args.entry_label} {year} - {args.asset_name}"
            )
            txn_date = args.annual_date or datetime.date(year, 12, 15)
            posting_lines = build_posting_lines(
                args.accum_account, args.expense_account, amount, args.currency
            )
            output_lines.extend(
                build_transaction(txn_date, narration, tags, posting_lines)
            )
            total_depreciation += amount
            continue

        sum_weights = sum(entry.weight for entry in entries)
        is_full_year = len(entries) == 12 and sum_weights == decimal.Decimal("12.0")
        if year == placed_month.year:
            if entries[0].month == placed_month.month and entries[-1].month == 12:
                expected_total = depreciation.calculate_first_year_depreciation(
                    args.cost_basis, args.recovery_years, placed_month.month
                )
            else:
                expected_total = (monthly * sum_weights).quantize(
                    decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
                )
        elif is_full_year:
            expected_total = annual
        else:
            expected_total = (monthly * sum_weights).quantize(
                decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
            )

        amounts = [
            (monthly * entry.weight).quantize(
                decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
            )
            for entry in entries
        ]

        base_total = sum(amounts)
        diff = base_total - expected_total
        diff_cents = cents_int(diff)

        if diff_cents != 0:
            adjust = decimal.Decimal("0.01") * (-1 if diff_cents > 0 else 1)
            for idx in range(abs(diff_cents)):
                target = len(amounts) - 1 - (idx % len(amounts))
                amounts[target] = (amounts[target] + adjust).quantize(
                    decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
                )

        for entry, amount in zip(entries, amounts):
            month_date = entry.year_month().to_date(args.monthly_day)
            narration = (
                args.narration
                if args.narration
                else f"Monthly {args.entry_label} - {args.asset_name}"
            )
            posting_lines = build_posting_lines(
                args.accum_account, args.expense_account, amount, args.currency
            )
            output_lines.extend(
                build_transaction(month_date, narration, tags, posting_lines)
            )
            total_depreciation += amount

    if args.include_balance:
        if args.balance_date:
            balance_date = args.balance_date
        elif args.year:
            balance_date = datetime.date(args.year, 12, 16)
        else:
            raise SystemExit("balance-date is required when using date ranges.")

        starting = args.starting_accumulated
        starting_balance = (
            starting if starting < 0 else (starting * decimal.Decimal("-1"))
        )
        final_balance = (starting_balance - total_depreciation).quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
        )
        max_len = len(args.accum_account)
        spaces = " " * max(2, (max_len + 2) - len(args.accum_account))
        output_lines.append(
            f"{balance_date.isoformat()} balance {args.accum_account}"
            f"{spaces}{format_amount(final_balance, args.currency)}"
        )

    print("\n".join(output_lines).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
