"""Fidelity brokerage CSV format parser."""

import csv
import datetime
import io
from decimal import Decimal
from typing import Optional

import beancount.core.data

from beanout.common import amounts, beancount_helpers, rendering
from beanout.entities.fidelity.config import FidelityConfig


def parse_csv_text(
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
        amount = amounts.parse_amount(amount_raw)
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


def render_csv_text(text: str, config: Optional[FidelityConfig] = None) -> str:
    """Render Fidelity CSV content into Beancount entries."""
    entries = parse_csv_text(text, config=config)
    return rendering.render_to_beancount(entries)


def render_csv_text_to_jsonl(text: str, config: Optional[FidelityConfig] = None) -> str:
    """Render Fidelity CSV content into JSONL format."""
    entries = parse_csv_text(text, config=config)
    return rendering.render_to_jsonl(entries)


def _iter_fidelity_rows(text: str) -> list[dict[str, str]]:
    """Parse Fidelity CSV rows, finding header and skipping preamble."""
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


def _build_narration(
    account_name: str, action: str, description: str, symbol: str
) -> str:
    """Build narration from CSV fields."""
    details = action or description or "Fidelity activity"
    if symbol and symbol not in details:
        details = f"{details} ({symbol})"
    if account_name:
        return f"{account_name}: {details}"
    return details


def _build_transaction(
    tx_date: datetime.date,
    narration: str,
    amount: Decimal,
    config: FidelityConfig,
) -> beancount.core.data.Transaction:
    """Build a transaction from CSV row data."""
    postings = _build_postings(amount, config)
    return beancount_helpers.create_transaction(
        date=tx_date,
        flag=config.flag,
        payee=config.payee,
        narration=narration,
        postings=postings,
        tags=set(config.tags),
    )


def _build_postings(
    amount: Decimal,
    config: FidelityConfig,
) -> list[beancount.core.data.Posting]:
    """Build postings for a transaction."""
    cash_posting = beancount_helpers.create_posting(
        config.account_cash, amount, config.currency
    )
    offset_posting = beancount_helpers.create_posting(
        config.account_offset, amounts.negate(amount), config.currency
    )

    # Sort: negative first, then positive
    if amount < 0:
        return [cash_posting, offset_posting]
    return [offset_posting, cash_posting]
