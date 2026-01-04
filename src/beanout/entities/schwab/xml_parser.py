"""Schwab bank XML format parser."""

import datetime
import xml.etree.ElementTree as ElementTree
from decimal import Decimal
from typing import Optional

import beancount.core.data

from beanout.common import amounts, beancount_helpers, rendering
from beanout.entities.schwab.config import SchwabConfig


def parse_xml_data(
    data: str | bytes, config: Optional[SchwabConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Schwab XML content into Beancount directives."""
    if config is None:
        config = SchwabConfig()

    root = _parse_xml_payload(data)
    entries: list[beancount.core.data.Directive] = []

    for tx in _iter_xml_transactions(root):
        date_raw = _xml_text(tx, "Date")
        if not date_raw:
            continue
        try:
            tx_date = datetime.datetime.strptime(date_raw, "%m/%d/%Y").date()
        except ValueError:
            continue

        withdrawal = _xml_text(tx, "Withdrawal")
        deposit = _xml_text(tx, "Deposit")
        amount = _select_amount(withdrawal, deposit)
        if amount == 0:
            continue

        description = _xml_text(tx, "Description")
        tx_type = _xml_text(tx, "Type")
        narration = _build_narration(description, tx_type)

        entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def render_xml_data(
    data: str | bytes, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab XML content into Beancount entries."""
    entries = parse_xml_data(data, config=config)
    return rendering.render_to_beancount(entries)


def render_xml_data_to_jsonl(
    data: str | bytes, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab XML content into JSONL format."""
    entries = parse_xml_data(data, config=config)
    return rendering.render_to_jsonl(entries)


def _parse_xml_payload(text: str | bytes) -> ElementTree.Element:
    """Parse XML payload, handling encoding issues."""
    if isinstance(text, bytes):
        payload = text
    else:
        payload = text.encode("utf-8")
    # Fix common encoding declaration issue
    if b"\x00" not in payload[:200]:
        lowered = payload[:200].lower()
        if b'encoding="utf-16"' in lowered:
            payload = payload.replace(b'encoding="utf-16"', b'encoding="utf-8"')
    return ElementTree.fromstring(payload)


def _iter_xml_transactions(
    root: ElementTree.Element,
) -> list[ElementTree.Element]:
    """Extract transaction elements from XML."""
    transactions: list[ElementTree.Element] = []
    for elem in root.iter():
        if elem.tag.endswith("NonPledgedAssetLinePostedTransaction"):
            transactions.append(elem)
    return transactions


def _xml_text(elem: ElementTree.Element, tag_name: str) -> str:
    """Extract text from XML element by tag name."""
    for child in list(elem):
        if child.tag.endswith(tag_name):
            return (child.text or "").strip()
    return ""


def _select_amount(withdrawal: str, deposit: str) -> Decimal:
    """Select amount from withdrawal or deposit field."""
    if deposit:
        return amounts.parse_amount(deposit)
    if withdrawal:
        return amounts.parse_amount(withdrawal) * Decimal("-1")
    return Decimal("0")


def _build_narration(description: str, tx_type: str) -> str:
    """Build narration from XML fields."""
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
    """Build a transaction from XML data."""
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
