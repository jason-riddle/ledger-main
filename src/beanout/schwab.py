"""Schwab bank JSON statement parsing and rendering."""

from __future__ import annotations

import dataclasses
import datetime
import json
import xml.etree.ElementTree as ElementTree
from decimal import Decimal
from typing import Optional

import beancount.core.amount
import beancount.core.data
import beancount.core.number

import beanout.formatter
import beanout.jsonl


@dataclasses.dataclass(frozen=True)
class SchwabConfig:
    """Default accounts and settings for Schwab parsing."""

    account_cash: str = "Assets:Cash---Bank:Schwab-Checking"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Schwab Bank"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "imported", "schwab")


def render_schwab_json_text(text: str, config: Optional[SchwabConfig] = None) -> str:
    """Render Schwab JSON content into Beancount entries."""
    entries = parse_schwab_json_text(text, config=config)
    return _render_entries(entries, config=config)


def render_schwab_xml_text(
    text: str | bytes, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab XML content into Beancount entries."""
    entries = parse_schwab_xml_text(text, config=config)
    return _render_entries(entries, config=config)


def render_schwab_json_file(
    filepath: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render a *.json Schwab file into Beancount text."""
    if not filepath.lower().endswith(".json"):
        raise ValueError("Input must be a .json file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_schwab_json_text(handle.read(), config=config)


def render_schwab_xml_file(filepath: str, config: Optional[SchwabConfig] = None) -> str:
    """Render a *.xml Schwab file into Beancount text."""
    if not filepath.lower().endswith(".xml"):
        raise ValueError("Input must be a .xml file")
    with open(filepath, "rb") as handle:
        return render_schwab_xml_text(handle.read(), config=config)


def render_schwab_json_text_to_jsonl(
    text: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab JSON content into JSONL format."""
    entries = parse_schwab_json_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_schwab_xml_text_to_jsonl(
    text: str | bytes, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab XML content into JSONL format."""
    entries = parse_schwab_xml_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_schwab_json_file_to_jsonl(
    filepath: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render a *.json Schwab file into JSONL format."""
    if not filepath.lower().endswith(".json"):
        raise ValueError("Input must be a .json file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_schwab_json_text_to_jsonl(handle.read(), config=config)


def render_schwab_xml_file_to_jsonl(
    filepath: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render a *.xml Schwab file into JSONL format."""
    if not filepath.lower().endswith(".xml"):
        raise ValueError("Input must be a .xml file")
    with open(filepath, "rb") as handle:
        return render_schwab_xml_text_to_jsonl(handle.read(), config=config)


def parse_schwab_json_text(
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


def parse_schwab_xml_text(
    text: str | bytes, config: Optional[SchwabConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Schwab XML content into Beancount directives."""
    if config is None:
        config = SchwabConfig()

    root = _parse_xml_payload(text)
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


def _select_amount(withdrawal: str, deposit: str) -> Decimal:
    if deposit:
        return _parse_amount(deposit)
    if withdrawal:
        return _parse_amount(withdrawal) * Decimal("-1")
    return beancount.core.number.D("0")


def _build_narration(description: str, tx_type: str) -> str:
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
    config: SchwabConfig,
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


def _parse_amount(amount_str: str) -> Decimal:
    cleaned = amount_str.replace("$", "").replace(",", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    return beancount.core.number.D(cleaned)


def _parse_xml_payload(text: str | bytes) -> ElementTree.Element:
    if isinstance(text, bytes):
        payload = text
    else:
        payload = text.encode("utf-8")
    if b"\x00" not in payload[:200]:
        lowered = payload[:200].lower()
        if b'encoding="utf-16"' in lowered:
            payload = payload.replace(b'encoding="utf-16"', b'encoding="utf-8"')
    return ElementTree.fromstring(payload)


def _iter_xml_transactions(
    root: ElementTree.Element,
) -> list[ElementTree.Element]:
    transactions: list[ElementTree.Element] = []
    for elem in root.iter():
        if elem.tag.endswith("NonPledgedAssetLinePostedTransaction"):
            transactions.append(elem)
    return transactions


def _xml_text(elem: ElementTree.Element, tag_name: str) -> str:
    for child in list(elem):
        if child.tag.endswith(tag_name):
            return (child.text or "").strip()
    return ""


def _render_entries(
    entries: list[beancount.core.data.Directive],
    config: Optional[SchwabConfig] = None,
) -> str:
    if config is None:
        config = SchwabConfig()

    # Use Beancount's native formatter for consistent output
    return beanout.formatter.format_entries(entries)

