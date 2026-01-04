"""Ally Bank statement parsing and rendering."""

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

import beanout.jsonl


@dataclasses.dataclass(frozen=True)
class AllyBankConfig:
    """Default accounts and settings for Ally Bank parsing."""

    account_cash: str = "Assets:Cash---Bank:Ally-Bank"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Ally Bank"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("ally-bank", "beangulp", "imported")


def render_ally_bank_csv_text(
    text: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render Ally Bank CSV content into Beancount entries."""
    entries = parse_ally_bank_csv_text(text, config=config)
    return _render_entries(entries, config=config)


def render_ally_bank_csv_file(
    filepath: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render a *.csv Ally Bank file into Beancount text."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_ally_bank_csv_text(handle.read(), config=config)


def render_ally_bank_csv_text_to_jsonl(
    text: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render Ally Bank CSV content into JSONL format."""
    entries = parse_ally_bank_csv_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_ally_bank_csv_file_to_jsonl(
    filepath: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render a *.csv Ally Bank file into JSONL format."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_ally_bank_csv_text_to_jsonl(handle.read(), config=config)


def parse_ally_bank_csv_text(
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

        amount = _parse_amount(amount_raw)
        if _is_withdrawal(tx_type) and amount > 0:
            amount = -amount
        if amount == 0:
            continue

        narration = _build_narration(tx_type, description)
        entries.append(_build_transaction(tx_date, narration, amount, config))

    return entries


def render_ally_bank_qfx_text(
    text: str | bytes, config: Optional[AllyBankConfig] = None
) -> str:
    """Render Ally Bank QFX content into Beancount entries."""
    entries = parse_ally_bank_qfx_text(text, config=config)
    return _render_entries(entries, config=config)


def render_ally_bank_qfx_file(
    filepath: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render a *.qfx Ally Bank file into Beancount text."""
    if not filepath.lower().endswith(".qfx"):
        raise ValueError("Input must be a .qfx file")
    with open(filepath, "rb") as handle:
        return render_ally_bank_qfx_text(handle.read(), config=config)


def render_ally_bank_qfx_text_to_jsonl(
    text: str | bytes, config: Optional[AllyBankConfig] = None
) -> str:
    """Render Ally Bank QFX content into JSONL format."""
    entries = parse_ally_bank_qfx_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_ally_bank_qfx_file_to_jsonl(
    filepath: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render a *.qfx Ally Bank file into JSONL format."""
    if not filepath.lower().endswith(".qfx"):
        raise ValueError("Input must be a .qfx file")
    with open(filepath, "rb") as handle:
        return render_ally_bank_qfx_text_to_jsonl(handle.read(), config=config)


def parse_ally_bank_qfx_text(
    text: str | bytes, config: Optional[AllyBankConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Ally Bank QFX content into Beancount directives."""
    if config is None:
        config = AllyBankConfig()

    if isinstance(text, bytes):
        payload = text
    else:
        payload = text.encode("utf-8")

    parser = OFXTree()
    parser.parse(io.BytesIO(payload))

    for severity in parser.findall(".//SEVERITY"):
        if severity.text:
            severity.text = severity.text.strip().upper()

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
        return "Ally Bank activity"
    return " - ".join(parts)


def _build_narration(tx_type: str, description: str) -> str:
    if tx_type and description:
        return f"{tx_type}: {description}"
    if description:
        return description
    if tx_type:
        return tx_type
    return "Ally Bank activity"


def _is_withdrawal(tx_type: str) -> bool:
    tx_type_lower = tx_type.strip().lower()
    return tx_type_lower in {"withdrawal", "debit", "payment"}


def _build_transaction(
    tx_date: datetime.date,
    narration: str,
    amount: Decimal,
    config: AllyBankConfig,
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
    config: AllyBankConfig,
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


def _ensure_decimal(value: Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return beancount.core.number.D(str(value))


def _render_entries(
    entries: list[beancount.core.data.Directive],
    config: Optional[AllyBankConfig] = None,
) -> str:
    if config is None:
        config = AllyBankConfig()

    lines: list[str] = []
    for entry in entries:
        if lines:
            lines.append("")
        lines.extend(_render_transaction(entry, config))
    return "\n".join(lines) + ("\n" if lines else "")


def _render_transaction(
    entry: beancount.core.data.Transaction, config: AllyBankConfig
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
    amount_end_col = 40
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
