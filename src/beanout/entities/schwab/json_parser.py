"""Schwab bank JSON format parser."""

import datetime
import json
from decimal import Decimal
from typing import Optional

import beancount.core.data

from beanout.common import amounts, beancount_helpers, rendering
from beanout.entities.schwab.config import SchwabConfig


def parse_json_text(
    text: str, config: Optional[SchwabConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Schwab JSON content into Beancount directives."""
    if config is None:
        config = SchwabConfig()

    data = json.loads(text)
    posted = data.get("PostedTransactions", []) or []

    entries: list[beancount.core.data.Directive] = []
    for tx in posted:
        date_raw = (tx.get("Date") or "").strip()
        if not date_raw:
            continue
        try:
            tx_date = datetime.datetime.strptime(date_raw, "%m/%d/%Y").date()
        except ValueError:
            continue

        withdrawal = (tx.get("Withdrawal") or "").strip()
        deposit = (tx.get("Deposit") or "").strip()
        amount = _select_amount(withdrawal, deposit)
        if amount == 0:
            continue

        description = (tx.get("Description") or "").strip()
        tx_type = (tx.get("Type") or "").strip()
        narration = _build_narration(description, tx_type)

        entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def render_json_text(text: str, config: Optional[SchwabConfig] = None) -> str:
    """Render Schwab JSON content into Beancount entries."""
    entries = parse_json_text(text, config=config)
    return rendering.render_to_beancount(entries)


def render_json_text_to_jsonl(text: str, config: Optional[SchwabConfig] = None) -> str:
    """Render Schwab JSON content into JSONL format."""
    entries = parse_json_text(text, config=config)
    return rendering.render_to_jsonl(entries)


def _select_amount(withdrawal: str, deposit: str) -> Decimal:
    """Select amount from withdrawal or deposit field."""
    if deposit:
        return amounts.parse_amount(deposit)
    if withdrawal:
        return amounts.parse_amount(withdrawal) * Decimal("-1")
    return Decimal("0")


def _build_narration(description: str, tx_type: str) -> str:
    """Build narration from JSON fields."""
    if tx_type and description:
        return f"{tx_type}: {description}"
    if description:
        return description
    if tx_type:
        return tx_type
    return "Schwab activity"


def _build_transaction(
    tx_date: datetime.date,
    narration: str,
    amount: Decimal,
    config: SchwabConfig,
) -> beancount.core.data.Transaction:
    """Build a transaction from JSON data."""
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
    config: SchwabConfig,
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
