"""Chase credit card statement parsing and rendering."""

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
from ofxtools.Parser import OFXTree

import beanout.formatter
import beanout.jsonl


@dataclasses.dataclass(frozen=True)
class ChaseConfig:
    """Default accounts and settings for Chase parsing."""

    account_credit: str = "Liabilities:Credit-Cards:Chase-9265"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Chase"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "chase", "imported")


def render_chase_csv_text(text: str, config: Optional[ChaseConfig] = None) -> str:
    """Render Chase CSV content into Beancount entries."""
    entries = parse_chase_csv_text(text, config=config)
    return _render_entries(entries, config=config)


def render_chase_csv_file(filepath: str, config: Optional[ChaseConfig] = None) -> str:
    """Render a *.csv Chase file into Beancount text."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_chase_csv_text(handle.read(), config=config)


def render_chase_csv_text_to_jsonl(
    text: str, config: Optional[ChaseConfig] = None
) -> str:
    """Render Chase CSV content into JSONL format."""
    entries = parse_chase_csv_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_chase_csv_file_to_jsonl(
    filepath: str, config: Optional[ChaseConfig] = None
) -> str:
    """Render a *.csv Chase file into JSONL format."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_chase_csv_text_to_jsonl(handle.read(), config=config)


def parse_chase_csv_text(
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

        amount = _parse_amount(amount_raw)
        if amount == 0:
            continue

        narration = _build_narration(description, category, tx_type, memo)
        entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def render_chase_qfx_text(
    text: str | bytes, config: Optional[ChaseConfig] = None
) -> str:
    """Render Chase QFX content into Beancount entries."""
    entries = parse_chase_qfx_text(text, config=config)
    return _render_entries(entries, config=config)


def render_chase_qfx_file(filepath: str, config: Optional[ChaseConfig] = None) -> str:
    """Render a *.qfx Chase file into Beancount text."""
    if not filepath.lower().endswith(".qfx"):
        raise ValueError("Input must be a .qfx file")
    with open(filepath, "rb") as handle:
        return render_chase_qfx_text(handle.read(), config=config)


def render_chase_qfx_text_to_jsonl(
    text: str | bytes, config: Optional[ChaseConfig] = None
) -> str:
    """Render Chase QFX content into JSONL format."""
    entries = parse_chase_qfx_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_chase_qfx_file_to_jsonl(
    filepath: str, config: Optional[ChaseConfig] = None
) -> str:
    """Render a *.qfx Chase file into JSONL format."""
    if not filepath.lower().endswith(".qfx"):
        raise ValueError("Input must be a .qfx file")
    with open(filepath, "rb") as handle:
        return render_chase_qfx_text_to_jsonl(handle.read(), config=config)


def parse_chase_qfx_text(
    text: str | bytes, config: Optional[ChaseConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Chase QFX content into Beancount directives."""
    if config is None:
        config = ChaseConfig()

    payload = text if isinstance(text, bytes) else text.encode("utf-8")
    parser = OFXTree()
    parser.parse(io.BytesIO(payload))
    ofx = parser.convert()

    entries: list[beancount.core.data.Directive] = []
    for statement in ofx.statements:
        for txn in statement.transactions:
            amount = _ensure_decimal(txn.trnamt)
            if amount == 0:
                continue
            tx_date = txn.dtposted.date()
            name = getattr(txn, "name", None) or ""
            memo = getattr(txn, "memo", None) or ""
            tx_type = getattr(txn, "trntype", None) or ""
            narration = _build_ofx_narration(tx_type, name, memo)
            entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def _build_ofx_narration(tx_type: str, name: str, memo: str) -> str:
    parts = [value for value in (tx_type, name, memo) if value]
    if not parts:
        return "Chase activity"
    return " - ".join(parts)


def _build_narration(
    description: str,
    category: str,
    tx_type: str,
    memo: str,
) -> str:
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
    config: ChaseConfig,
) -> list[beancount.core.data.Posting]:
    units_credit = beancount.core.amount.Amount(amount, config.currency)
    units_offset = beancount.core.amount.Amount(-amount, config.currency)

    credit_posting = beancount.core.data.Posting(
        config.account_credit,
        units_credit,
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
        return [credit_posting, offset_posting]
    return [offset_posting, credit_posting]


def _parse_amount(amount_str: str) -> Decimal:
    cleaned = amount_str.replace("$", "").replace(",", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = f"-{cleaned[1:-1]}"
    return beancount.core.number.D(cleaned)


def _ensure_decimal(value: Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return beancount.core.number.D(str(value))


def _render_entries(
    entries: list[beancount.core.data.Directive],
    config: Optional[ChaseConfig] = None,
) -> str:
    if config is None:
        config = ChaseConfig()

    # Use Beancount's native formatter for consistent output
    return beanout.formatter.format_entries(entries)
