"""Schwab bank JSON statement parsing and rendering."""

from __future__ import annotations

import dataclasses
import datetime
import json
from decimal import Decimal
from typing import Optional

import beancount.core.amount
import beancount.core.data
import beancount.core.number

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


def render_schwab_json_file(
    filepath: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render a *.json Schwab file into Beancount text."""
    if not filepath.endswith(".json"):
        raise ValueError("Input must be a .json file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_schwab_json_text(handle.read(), config=config)


def render_schwab_json_text_to_jsonl(
    text: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab JSON content into JSONL format."""
    entries = parse_schwab_json_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_schwab_json_file_to_jsonl(
    filepath: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render a *.json Schwab file into JSONL format."""
    if not filepath.endswith(".json"):
        raise ValueError("Input must be a .json file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_schwab_json_text_to_jsonl(handle.read(), config=config)


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


def _render_entries(
    entries: list[beancount.core.data.Directive],
    config: Optional[SchwabConfig] = None,
) -> str:
    if config is None:
        config = SchwabConfig()

    lines: list[str] = []
    for entry in entries:
        if lines:
            lines.append("")
        lines.extend(_render_transaction(entry, config))
    return "\n".join(lines) + ("\n" if lines else "")


def _render_transaction(
    entry: beancount.core.data.Transaction, config: SchwabConfig
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
