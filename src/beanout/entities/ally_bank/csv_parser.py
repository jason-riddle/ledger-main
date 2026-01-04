"""Ally Bank CSV format parser."""

import csv
import datetime
import io
from decimal import Decimal
from typing import Optional

import beancount.core.data

from beanout.common import amounts, beancount_helpers, rendering
from beanout.entities.ally_bank.config import AllyBankConfig


def parse_csv_text(
    text: str, config: Optional[AllyBankConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Ally Bank CSV content into Beancount directives."""
    if config is None:
        config = AllyBankConfig()

    entries: list[beancount.core.data.Directive] = []
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return entries

    header = [col.strip().lower() for col in rows[0]]
    if header[:5] != ["date", "time", "amount", "type", "description"]:
        raise ValueError("Unexpected Ally Bank CSV header")

    for row in rows[1:]:
        if len(row) < 5:
            continue
        date_raw, _, amount_raw, tx_type, description = [col.strip() for col in row[:5]]
        try:
            tx_date = datetime.datetime.strptime(date_raw, "%Y-%m-%d").date()
        except ValueError:
            continue

        amount = amounts.parse_amount(amount_raw)
        if _is_withdrawal(tx_type) and amount > 0:
            amount = -amount
        if amount == 0:
            continue

        narration = _build_narration(tx_type, description)
        entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def render_csv_text(text: str, config: Optional[AllyBankConfig] = None) -> str:
    """Render Ally Bank CSV content into Beancount entries."""
    entries = parse_csv_text(text, config=config)
    return rendering.render_to_beancount(entries)


def render_csv_text_to_jsonl(text: str, config: Optional[AllyBankConfig] = None) -> str:
    """Render Ally Bank CSV content into JSONL format."""
    entries = parse_csv_text(text, config=config)
    return rendering.render_to_jsonl(entries)


def _build_narration(tx_type: str, description: str) -> str:
    """Build narration from CSV fields."""
    if tx_type and description:
        return f"{tx_type}: {description}"
    if description:
        return description
    if tx_type:
        return tx_type
    return "Ally Bank activity"


def _is_withdrawal(tx_type: str) -> bool:
    """Check if transaction type indicates a withdrawal."""
    tx_type_lower = tx_type.strip().lower()
    return tx_type_lower in {"withdrawal", "debit", "payment"}


def _build_transaction(
    tx_date: datetime.date,
    narration: str,
    amount: Decimal,
    config: AllyBankConfig,
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
    config: AllyBankConfig,
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
