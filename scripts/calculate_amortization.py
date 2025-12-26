#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = [
# ]
# ///

"""
Calculate loan amortization details and emit JSON.

Outputs include:
- summary: monthly payment, total interest, total paid (full term)
- point: details for a single month (by number or date)
- range: details for a month range (by number or date)
"""

import argparse
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional, Tuple

from utils.amortization import (
    calculate_monthly_payment,
    generate_amortization_schedule,
)


@dataclass(frozen=True)
class YearMonth:
    year: int
    month: int

    def to_date(self) -> date:
        return date(self.year, self.month, 1)


def parse_year_month(value: str) -> YearMonth:
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


def month_index_from_start(start: YearMonth, target: YearMonth) -> int:
    start_total = start.year * 12 + (start.month - 1)
    target_total = target.year * 12 + (target.month - 1)
    return (target_total - start_total) + 1


def clamp_month_range(start: int, end: int, total_months: int) -> Tuple[int, int]:
    if start < 1 or end < 1:
        raise ValueError("Month range must be >= 1.")
    if start > end:
        raise ValueError("from must be <= to.")
    if end > total_months:
        raise ValueError("Range exceeds term length.")
    return start, end


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate amortization details.")
    parser.add_argument("--principal", type=float, required=True)
    parser.add_argument("--annual-rate", type=float, required=True)
    parser.add_argument("--term-years", type=int, required=True)

    parser.add_argument("--start-date", type=parse_year_month)
    parser.add_argument("--start-month", type=int, default=1)

    parser.add_argument("--month", type=int, help="1-based month number")
    parser.add_argument("--date", type=parse_year_month, help="YYYY-MM")

    parser.add_argument("--from-month", type=int, help="1-based range start")
    parser.add_argument("--to-month", type=int, help="1-based range end")
    parser.add_argument("--from-date", type=parse_year_month, help="YYYY-MM")
    parser.add_argument("--to-date", type=parse_year_month, help="YYYY-MM")

    parser.add_argument("--full-schedule", action="store_true")

    return parser.parse_args()


def decimal_to_str(value: Decimal) -> str:
    return f"{value:.2f}"


def serialize_entry(entry: dict) -> dict:
    return {
        "month": entry["month"],
        "balance_before": decimal_to_str(entry["balance_before"]),
        "payment": decimal_to_str(entry["payment"]),
        "interest": decimal_to_str(entry["interest"]),
        "principal": decimal_to_str(entry["principal"]),
        "balance_after": decimal_to_str(entry["balance_after"]),
    }


def total_interest(schedule: Iterable[dict]) -> Decimal:
    total = Decimal("0")
    for entry in schedule:
        total += entry["interest"]
    return total


def total_payments(schedule: Iterable[dict]) -> Decimal:
    total = Decimal("0")
    for entry in schedule:
        total += entry["payment"]
    return total


def main() -> int:
    args = parse_args()

    if args.term_years <= 0:
        raise SystemExit("term-years must be positive.")

    uses_dates = any([args.date, args.from_date, args.to_date])
    if uses_dates and not args.start_date:
        raise SystemExit("start-date is required when using date-based options.")

    if args.start_date:
        start = args.start_date
    else:
        if args.start_month < 1 or args.start_month > 12:
            raise SystemExit("start-month must be between 1 and 12.")
        start = YearMonth(year=1970, month=args.start_month)

    total_months = args.term_years * 12

    schedule = generate_amortization_schedule(
        args.principal,
        args.annual_rate,
        args.term_years,
        start_month=1,
    )

    payment = calculate_monthly_payment(
        args.principal, args.annual_rate, args.term_years
    )
    interest_total = total_interest(schedule)
    paid_total = total_payments(schedule)

    output = {
        "summary": {
            "monthly_payment": decimal_to_str(payment),
            "total_interest": decimal_to_str(interest_total),
            "total_paid": decimal_to_str(paid_total),
            "term_months": total_months,
        }
    }

    point_month: Optional[int] = None
    if args.date:
        point_month = month_index_from_start(start, args.date)
    elif args.month:
        point_month = args.month

    if point_month is not None:
        if point_month < 1 or point_month > total_months:
            raise SystemExit("month is out of range for the loan term.")
        output["point"] = serialize_entry(schedule[point_month - 1])

    range_start: Optional[int] = None
    range_end: Optional[int] = None
    if args.from_date or args.to_date:
        if not (args.from_date and args.to_date):
            raise SystemExit("from-date and to-date must be provided together.")
        range_start = month_index_from_start(start, args.from_date)
        range_end = month_index_from_start(start, args.to_date)
    elif args.from_month or args.to_month:
        if args.from_month is None or args.to_month is None:
            raise SystemExit("from-month and to-month must be provided together.")
        range_start = args.from_month
        range_end = args.to_month

    if range_start is not None and range_end is not None:
        try:
            start_idx, end_idx = clamp_month_range(range_start, range_end, total_months)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        output["range"] = [
            serialize_entry(entry) for entry in schedule[start_idx - 1 : end_idx]
        ]

    if args.full_schedule:
        output["schedule"] = [serialize_entry(entry) for entry in schedule]

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
