"""Fidelity brokerage CSV parsing and rendering."""

from __future__ import annotations

import csv
import dataclasses
import datetime
import io
from decimal import Decimal
from typing import Optional

import beancount.core.amount
import beancount.core.data
import beancount.core.number

import beanout.jsonl


@dataclasses.dataclass(frozen=True)
class FidelityConfig:
    """Default accounts and settings for Fidelity parsing."""

    account_cash: str = "Assets:Investments:Fidelity:Cash"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Fidelity"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "imported", "fidelity")


def render_fidelity_csv_text(text: str, config: Optional[FidelityConfig] = None) -> str:
    """Render Fidelity CSV content into Beancount entries."""
    entries = parse_fidelity_csv_text(text, config=config)
    return _render_entries(entries, config=config)


def render_fidelity_csv_file(
    filepath: str, config: Optional[FidelityConfig] = None
) -> str:
    """Render a *.csv Fidelity file into Beancount text."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8-sig") as handle:
        return render_fidelity_csv_text(handle.read(), config=config)


def render_fidelity_csv_text_to_jsonl(
    text: str, config: Optional[FidelityConfig] = None
) -> str:
    """Render Fidelity CSV content into JSONL format."""
    entries = parse_fidelity_csv_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_fidelity_csv_file_to_jsonl(
    filepath: str, config: Optional[FidelityConfig] = None
) -> str:
    """Render a *.csv Fidelity file into JSONL format."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8-sig") as handle:
        return render_fidelity_csv_text_to_jsonl(handle.read(), config=config)


def parse_fidelity_csv_text(
    text: str, config: Optional[FidelityConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Fidelity CSV content into Beancount directives."""
    if config is None:
        config = FidelityConfig()

    entries: list[beancount.core.data.Directive] = []
    for row in _iter_fidelity_rows(text):
        run_date = (row.get("Run Date") or "").strip()
        if not run_date:
            continue
        try:
            tx_date = datetime.datetime.strptime(run_date, "%m/%d/%Y").date()
        except ValueError:
            continue

        amount_raw = (row.get("Amount") or "").strip()
        if not amount_raw:
            continue
        amount = _parse_amount(amount_raw)
        if amount == 0:
            continue

        action = (row.get("Action") or "").strip()
        account_name = (row.get("Account") or "").strip()
        description = (row.get("Description") or "").strip()
        symbol = (row.get("Symbol") or "").strip()

        narration = _build_narration(account_name, action, description, symbol)
        txn = _build_transaction(tx_date, narration, amount, config)
        entries.append(txn)

    return entries


def _iter_fidelity_rows(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    header_index = None
    for idx, line in enumerate(lines):
        cleaned = line.lstrip("\ufeff").strip()
        if cleaned.startswith("Run Date,"):
            header_index = idx
            break

    if header_index is None:
        raise ValueError("Fidelity CSV header not found")

    csv_text = "\n".join(lines[header_index:])
    reader = csv.DictReader(io.StringIO(csv_text))
    rows: list[dict[str, str]] = []
    for row in reader:
        if not row:
            continue
        if not any((value or "").strip() for value in row.values()):
            continue
        rows.append(row)
    return rows


def _build_transaction(
    tx_date: datetime.date,
    narration: str,
    amount: Decimal,
    config: FidelityConfig,
) -> beancount.core.data.Transaction:
    postings = _build_postings(amount, config)
    return beancount.core.data.Transaction(
        meta={},
        date=tx_date,
        flag=config.flag,
        payee=config.payee,
        narration=narration,
        tags=set(config.tags),
        links=set(),
        postings=postings,
    )


def _build_postings(
    amount: Decimal,
    config: FidelityConfig,
) -> list[beancount.core.data.Posting]:
    units_cash = beancount.core.amount.Amount(amount, config.currency)
    units_offset = beancount.core.amount.Amount(-amount, config.currency)

    cash_posting = beancount.core.data.Posting(
        config.account_cash,
        units_cash,
        None,
        None,
        None,
        None,
    )
    offset_posting = beancount.core.data.Posting(
        config.account_offset,
        units_offset,
        None,
        None,
        None,
        None,
    )

    if amount < 0:
        return [cash_posting, offset_posting]
    return [offset_posting, cash_posting]


def _build_narration(
    account_name: str, action: str, description: str, symbol: str
) -> str:
    details = action or description or "Fidelity activity"
    if symbol and symbol not in details:
        details = f"{details} ({symbol})"
    if account_name:
        return f"{account_name}: {details}"
    return details


def _parse_amount(amount_str: str) -> Decimal:
    cleaned = amount_str.replace(",", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    return beancount.core.number.D(cleaned)


def _render_entries(
    entries: list[beancount.core.data.Directive],
    config: Optional[FidelityConfig] = None,
) -> str:
    if config is None:
        config = FidelityConfig()

    lines: list[str] = []
    for entry in entries:
        if lines:
            lines.append("")
        lines.extend(_render_transaction(entry, config))
    return "\n".join(lines) + ("\n" if lines else "")


def _render_transaction(
    entry: beancount.core.data.Transaction, config: FidelityConfig
) -> list[str]:
    tags = " ".join(f"#{tag}" for tag in sorted(entry.tags))
    header = (
        f'{entry.date.isoformat()} {entry.flag} "{entry.payee}" "{entry.narration}"'
    )
    if tags:
        header = f"{header} {tags}"

    lines = [header]
    for posting in entry.postings:
        amount_str = _format_amount(posting.units.number)
        prefix = f"  {posting.account}"
        lines.append(_format_account_line(prefix, amount_str, config.currency))
    return lines


def _format_account_line(prefix: str, amount: str, currency: str) -> str:
    amount_end_col = 69
    spaces = amount_end_col - len(prefix) - len(amount)
    if spaces < 1:
        spaces = 1
    return f"{prefix}{' ' * spaces}{amount} {currency}"


def _format_amount(value: Decimal) -> str:
    if value == 0:
        return "0"

    is_negative = value < 0
    magnitude = -value if is_negative else value
    formatted = f"{magnitude:.2f}"
    return f"-{formatted}" if is_negative else formatted
