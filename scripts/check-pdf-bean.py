#!/usr/bin/env python3
"""Check .pdf.txt transactions are represented in matching .pdf.bean files.

Usage:
  scripts/check-pdf-bean.py
  scripts/check-pdf-bean.py --root fixtures/golden
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

AMOUNT_RE = re.compile(r"\(?-?\$?\s*[\d,]+\.\d{2}\)?")
DATE_MDY_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b")
DATE_MDY_DASH_RE = re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b")


def _norm_amount(raw: str) -> str:
    negative = "-" in raw or ("(" in raw and ")" in raw)
    num_match = re.search(r"[\d,]+\.\d{2}", raw)
    if not num_match:
        return ""
    value = Decimal(num_match.group(0).replace(",", ""))
    if negative:
        value = -value
    value = abs(value).quantize(Decimal("0.01"))
    return f"{value:.2f}"


def _extract_amounts(line: str, *, include_zero: bool) -> list[str]:
    amounts: list[str] = []
    for match in AMOUNT_RE.findall(line):
        value = _norm_amount(match)
        if not value:
            continue
        if not include_zero and value == "0.00":
            continue
        amounts.append(value)
    return amounts


def _statement_year(txt: str) -> int | None:
    match = re.search(
        r"Statement Date[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-]([0-9]{4}))", txt
    )
    if match:
        return int(match.group(2))
    match = re.search(r"Statement date\s*([0-9]{1,2}/[0-9]{1,2}/([0-9]{4}))", txt)
    if match:
        return int(match.group(2))
    return None


def _detect_kind(txt: str) -> str:
    if "Detail tr an saction s" in txt or "Detail transactions" in txt:
        return "sheer_value"
    if "TRANSACTION DETAILS" in txt:
        return "clover_leaf"
    if "Transaction Activity" in txt:
        return "sps"
    return "generic"


def _parse_pdf_transactions(path: Path) -> tuple[str, list[tuple[str, list[str], str]]]:
    txt = path.read_text()
    year_hint = _statement_year(txt)
    kind = _detect_kind(txt)

    txns: list[tuple[str, list[str], str]] = []
    in_section = False

    for line in txt.splitlines():
        line_stripped = line.strip()

        if kind == "sheer_value":
            if "Detail tr an saction s" in line or "Detail transactions" in line:
                in_section = True
                continue
            if in_section:
                if line_stripped.startswith("Ending cash balance"):
                    in_section = False
                    continue
                if re.match(r"\s*\d{1,2}/\d{1,2}/\d{4}\s+", line):
                    amounts = _extract_amounts(line, include_zero=False)
                    if len(amounts) >= 2:
                        amount = amounts[-2]
                        match = DATE_MDY_RE.search(line)
                        if match:
                            month, day, year = map(int, match.groups())
                            date = f"{year:04d}-{month:02d}-{day:02d}"
                            txns.append((date, [amount], line_stripped))

        elif kind == "clover_leaf":
            if "TRANSACTION DETAILS" in line:
                in_section = True
                continue
            if in_section:
                if line_stripped in {
                    "MANAGED UNITS",
                    "WORK ORDER",
                    "WORK ORDERS",
                } or line_stripped.startswith("Work Order #"):
                    in_section = False
                    continue
                match = DATE_MDY_DASH_RE.search(line)
                if match:
                    amounts_all = _extract_amounts(line, include_zero=True)
                    if amounts_all:
                        amounts = [a for a in amounts_all[:2] if a != "0.00"]
                        if amounts:
                            month, day, year = map(int, match.groups())
                            date = f"{year:04d}-{month:02d}-{day:02d}"
                            txns.append((date, amounts, line_stripped))

        elif kind == "sps":
            if "Transaction Activity" in line:
                in_section = True
                continue
            if in_section:
                if line_stripped.startswith("Past Payments Breakdown"):
                    in_section = False
                    continue
                match = DATE_MDY_RE.search(line)
                if match and _extract_amounts(line, include_zero=True):
                    month, day, year = match.groups()
                    if year is None:
                        year = year_hint
                    if year is None:
                        continue
                    date = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                    amounts = _extract_amounts(line, include_zero=True)
                    if len(amounts) >= 2:
                        amounts = amounts[:-1]
                    amounts = [a for a in amounts if a != "0.00"]
                    if amounts:
                        txns.append((date, amounts, line_stripped))

        else:
            match = DATE_MDY_RE.search(line) or DATE_MDY_DASH_RE.search(line)
            if match and _extract_amounts(line, include_zero=False):
                if len(match.groups()) == 3:
                    month, day, year = match.groups()
                else:
                    month, day, year = match.group(1), match.group(2), match.group(3)
                date = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                amounts = _extract_amounts(line, include_zero=False)
                txns.append((date, amounts, line_stripped))

    return kind, txns


def _parse_bean_amounts(path: Path) -> dict[str, Counter[str]]:
    txt = path.read_text()
    date_amounts: dict[str, Counter[str]] = defaultdict(Counter)

    lines = txt.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^(\d{4}-\d{2}-\d{2})\s", line)
        if match:
            current_date = match.group(1)
            for amount in _extract_amounts(line, include_zero=False):
                date_amounts[current_date][amount] += 1
            i += 1
            while i < len(lines):
                pline = lines[i]
                if re.match(r"^\d{4}-\d{2}-\d{2}\s", pline):
                    i -= 1
                    break
                if pline.startswith(" ") or pline.startswith("\t"):
                    for amount in _extract_amounts(pline, include_zero=False):
                        date_amounts[current_date][amount] += 1
                i += 1
        i += 1

    return date_amounts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify .pdf.txt transactions exist in .pdf.bean files."
    )
    parser.add_argument(
        "--root",
        default="fixtures/golden",
        help="Root directory to search for .pdf.txt files (default: fixtures/golden)",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Root path does not exist: {root}")
        return 2

    pdf_files = sorted(root.rglob("*.pdf.txt"))
    if not pdf_files:
        print(f"No .pdf.txt files found under {root}")
        return 1

    overall_missing = False

    for path in pdf_files:
        bean_path = Path(str(path).replace(".pdf.txt", ".pdf.bean"))
        print(f"\n== {path} ==")
        if not bean_path.exists():
            print(f"MISSING bean file: {bean_path}")
            overall_missing = True
            continue

        kind, pdf_txns = _parse_pdf_transactions(path)
        bean_amounts = _parse_bean_amounts(bean_path)

        missing: list[tuple[str, list[str], str]] = []
        for date, amounts, line in pdf_txns:
            counter = bean_amounts.get(date)
            if not counter:
                missing.append((date, amounts, line))
                continue
            ok = True
            for amount in amounts:
                if counter[amount] <= 0:
                    ok = False
                    break
            if ok:
                for amount in amounts:
                    counter[amount] -= 1
            else:
                missing.append((date, amounts, line))

        print(f"type: {kind}")
        print(f"pdf lines: {len(pdf_txns)}")
        if missing:
            overall_missing = True
            print("missing:")
            for date, amounts, line in missing:
                print(f"  {date} {amounts} :: {line}")
        else:
            print("missing: none")

    return 1 if overall_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
