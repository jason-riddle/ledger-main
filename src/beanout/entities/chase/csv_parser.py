"""Chase credit card CSV format parser."""

import csv
import datetime
import io
from decimal import Decimal
from typing import Optional

import beancount.core.data

from beanout.common import amounts, beancount_helpers, rendering
from beanout.entities.chase.config import ChaseConfig


def parse_csv_text(
    text: str, config: Optional[ChaseConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Chase CSV content into Beancount directives."""
    if config is None:
        config = ChaseConfig()

    entries: list[beancount.core.data.Directive] = []
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return entries

    header = [col.strip().lower() for col in rows[0]]
    if header[:7] != [
        "transaction date",
        "post date",
        "description",
        "category",
        "type",
        "amount",
        "memo",
    ]:
        raise ValueError("Unexpected Chase CSV header")

    for row in rows[1:]:
        if len(row) < 7:
            continue
        (
            tx_date_raw,
            _,
            description,
            category,
            tx_type,
            amount_raw,
            memo,
        ) = [col.strip() for col in row[:7]]
        if not tx_date_raw:
            continue
        try:
            tx_date = datetime.datetime.strptime(tx_date_raw, "%m/%d/%Y").date()
        except ValueError:
            continue

        amount = amounts.parse_amount(amount_raw)
        if amount == 0:
            continue

        narration = _build_narration(description, category, tx_type, memo)
        entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def render_csv_text(text: str, config: Optional[ChaseConfig] = None) -> str:
    """Render Chase CSV content into Beancount entries."""
    entries = parse_csv_text(text, config=config)
    return rendering.render_to_beancount(entries)


def render_csv_text_to_jsonl(text: str, config: Optional[ChaseConfig] = None) -> str:
    """Render Chase CSV content into JSONL format."""
    entries = parse_csv_text(text, config=config)
    return rendering.render_to_jsonl(entries)


def _build_narration(
    description: str,
    category: str,
    tx_type: str,
    memo: str,
) -> str:
    """Build narration from CSV fields."""
    details = description or "Chase activity"
    if category:
        details = f"{details} [{category}]"
    if memo:
        details = f"{details} - {memo}"
    if tx_type:
        return f"{tx_type}: {details}"
    return details


def _build_transaction(
    tx_date: datetime.date,
    narration: str,
    amount: Decimal,
    config: ChaseConfig,
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
    config: ChaseConfig,
) -> list[beancount.core.data.Posting]:
    """Build postings for a transaction."""
    credit_posting = beancount_helpers.create_posting(
        config.account_credit, amount, config.currency
    )
    offset_posting = beancount_helpers.create_posting(
        config.account_offset, amounts.negate(amount), config.currency
    )

    # Sort: negative first, then positive
    if amount < 0:
        return [credit_posting, offset_posting]
    return [offset_posting, credit_posting]
