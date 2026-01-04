"""Chase credit card QFX/OFX format parser."""

import datetime
from decimal import Decimal
from typing import Optional

import beancount.core.data

from beanout.common import amounts, beancount_helpers, ofx, rendering
from beanout.entities.chase.config import ChaseConfig


def parse_qfx_data(
    data: str | bytes, config: Optional[ChaseConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Chase QFX content into Beancount directives."""
    if config is None:
        config = ChaseConfig()

    ofx_data = ofx.parse_ofx_data(data)

    entries: list[beancount.core.data.Directive] = []
    for statement in ofx_data.statements:
        for txn in statement.transactions:
            amount = amounts.ensure_decimal(txn.trnamt)
            if amount == 0:
                continue
            tx_date = txn.dtposted.date()
            name = getattr(txn, "name", None) or ""
            memo = getattr(txn, "memo", None) or ""
            tx_type = getattr(txn, "trntype", None) or ""
            narration = ofx.build_ofx_narration(tx_type, name, memo, "Chase activity")
            entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def render_qfx_data(
    data: str | bytes, config: Optional[ChaseConfig] = None
) -> str:
    """Render Chase QFX content into Beancount entries."""
    entries = parse_qfx_data(data, config=config)
    return rendering.render_to_beancount(entries)


def render_qfx_data_to_jsonl(
    data: str | bytes, config: Optional[ChaseConfig] = None
) -> str:
    """Render Chase QFX content into JSONL format."""
    entries = parse_qfx_data(data, config=config)
    return rendering.render_to_jsonl(entries)


def _build_transaction(
    tx_date: datetime.date,
    narration: str,
    amount: Decimal,
    config: ChaseConfig,
) -> beancount.core.data.Transaction:
    """Build a transaction from QFX data."""
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
