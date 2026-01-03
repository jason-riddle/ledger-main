"""CloverLeaf Property Management statement parsing and rendering."""

from __future__ import annotations

import dataclasses
import datetime
import re
from decimal import Decimal
from typing import Optional

import beancount.core.amount
import beancount.core.data
import beancount.core.number

import beanout.jsonl


@dataclasses.dataclass(frozen=True)
class CloverLeafConfig:
    """Default accounts and settings for CloverLeaf parsing."""

    account_property_management: str = "Assets:Property-Management:CloverLeaf-PM"
    account_opening: str = "Equity:Opening-Balances"
    account_owner_distribution: str = "Equity:Owner-Distributions:Owner-Draw"
    payee_management: str = "CloverLeaf Property Management"
    payee_tenant: str = "Tenant"
    payee_contractor: str = "Contractor"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "imported")


_DATE_RE = re.compile(r"\b\d{2}-\d{2}-\d{4}\b")
_PERIOD_RE = re.compile(r"(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})")

_PROPERTY_TAGS = {
    "2943-Butterfly-Palm": "2943-butterfly-palm",
    "206-Hoover-Ave": "206-hoover-ave",
}


def render_clover_leaf_text(
    text: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render CloverLeaf statement text into Beancount entries."""
    entries = parse_clover_leaf_text(text, config=config)
    return _render_entries(entries, config=config)


def render_clover_leaf_file(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.pdf.txt CloverLeaf file into Beancount text."""
    if not filepath.endswith(".pdf.txt"):
        raise ValueError("Input must be a .pdf.txt file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_text(handle.read(), config=config)


def render_clover_leaf_text_to_jsonl(
    text: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render CloverLeaf statement text into JSONL format."""
    entries = parse_clover_leaf_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_clover_leaf_file_to_jsonl(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.pdf.txt CloverLeaf file into JSONL format."""
    if not filepath.endswith(".pdf.txt"):
        raise ValueError("Input must be a .pdf.txt file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_text_to_jsonl(handle.read(), config=config)


def parse_clover_leaf_text(
    text: str, config: Optional[CloverLeafConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse CloverLeaf statement text into Beancount directives."""
    if config is None:
        config = CloverLeafConfig()

    period = _parse_statement_period(text)
    beginning_balance, ending_balance = _parse_summary_balances(text)

    in_details = False
    current_property: Optional[str] = None
    current_owner: Optional[str] = None
    entries: list[beancount.core.data.Directive] = []

    if period and beginning_balance is not None:
        entries.append(
            _build_balance(
                period[0], config.account_property_management, beginning_balance, config
            )
        )

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        stripped = line.strip()

        if not in_details:
            if stripped == "TRANSACTION DETAILS":
                in_details = True
            continue

        if stripped in {"OPEN WORK ORDERS", "MANAGED UNITS"}:
            break

        if "2943 Butterfly Palm" in stripped:
            current_property = "2943-Butterfly-Palm"
            continue
        if "206 Hoover Ave" in stripped:
            current_property = "206-Hoover-Ave"
            continue
        if stripped == "Jason Riddle":
            current_owner = "Jason Riddle"
            current_property = None
            continue

        if not _DATE_RE.search(stripped):
            continue

        entry = _parse_transaction_line(
            stripped, current_property, current_owner, config
        )
        if entry is not None:
            entries.append(entry)

    if period and ending_balance is not None:
        entries.append(
            _build_balance(
                period[1], config.account_property_management, ending_balance, config
            )
        )

    return entries


def _parse_transaction_line(
    line: str,
    current_property: Optional[str],
    current_owner: Optional[str],
    config: CloverLeafConfig,
) -> Optional[beancount.core.data.Transaction]:
    date_match = _DATE_RE.search(line)
    if not date_match:
        return None

    desc = line[: date_match.start()].strip()
    desc_upper = desc.upper()
    tx_date = datetime.datetime.strptime(date_match.group(0), "%m-%d-%Y").date()

    amounts = _extract_amounts(line)
    if len(amounts) < 2:
        return None

    increase = _parse_amount(amounts[0])
    decrease = _parse_amount(amounts[1])
    net_amount = increase - decrease

    if "OWNER DISTRIBUTION" in desc_upper:
        payee = current_owner or "Owner"
        return _build_owner_distribution(tx_date, payee, net_amount, config)

    account, payee = _categorize_transaction(desc_upper, current_property, config)
    if account is None or payee is None:
        return None

    tags = set(config.tags)
    if current_property:
        tags.add(_PROPERTY_TAGS[current_property])

    return _build_transaction(
        tx_date, payee, f"Memo: {desc}", tags, net_amount, account, config
    )


def _categorize_transaction(
    desc_upper: str,
    current_property: Optional[str],
    config: CloverLeafConfig,
) -> tuple[Optional[str], Optional[str]]:
    if not current_property:
        return None, None

    if desc_upper.startswith("RENT - RENT"):
        account = f"Income:Rent:{current_property}"
        return account, config.payee_tenant

    if "MANAGEMENT FEE EXPENSE" in desc_upper:
        account = f"Expenses:Management-Fees:{current_property}"
        return account, config.payee_management

    if "UTILITIES - ELECTRIC/GAS BILL" in desc_upper:
        account = f"Expenses:Utilities:Electric:{current_property}"
        return account, config.payee_management

    if "UTILITIES - WATER BILL" in desc_upper:
        account = f"Expenses:Utilities:Water:{current_property}"
        return account, config.payee_management

    if "LOCK CHANGE" in desc_upper or "GENERAL REPAIRS" in desc_upper:
        account = f"Expenses:Repairs:{current_property}"
        return account, config.payee_contractor

    if desc_upper.startswith("EGM MAINTENANCE"):
        account = f"Expenses:Repairs:{current_property}"
        return account, config.payee_contractor

    return None, None


def _build_balance(
    tx_date: datetime.date,
    account: str,
    amount: Decimal,
    config: CloverLeafConfig,
) -> beancount.core.data.Balance:
    meta = beancount.core.data.new_metadata("beanout", 0)
    return beancount.core.data.Balance(
        meta,
        tx_date,
        account,
        beancount.core.amount.Amount(amount, config.currency),
        None,
        None,
    )


def _build_owner_distribution(
    tx_date: datetime.date,
    payee: str,
    net_amount: Decimal,
    config: CloverLeafConfig,
) -> beancount.core.data.Transaction:
    meta = beancount.core.data.new_metadata("beanout", 0)
    tags = set(config.tags)
    tags.add("distributions")
    postings = [
        _posting(config.account_property_management, net_amount, config),
        _posting(config.account_owner_distribution, _negate(net_amount), config),
    ]
    postings = _sorted_postings(postings)
    return beancount.core.data.Transaction(
        meta,
        tx_date,
        config.flag,
        payee,
        "Memo: Owner Distribution",
        frozenset(tags),
        beancount.core.data.EMPTY_SET,
        postings,
    )


def _build_transaction(
    tx_date: datetime.date,
    payee: str,
    narration: str,
    tags: set[str],
    net_amount: Decimal,
    account: str,
    config: CloverLeafConfig,
) -> beancount.core.data.Transaction:
    meta = beancount.core.data.new_metadata("beanout", 0)
    postings = [
        _posting(config.account_property_management, net_amount, config),
        _posting(account, _negate(net_amount), config),
    ]
    postings = _sorted_postings(postings)
    return beancount.core.data.Transaction(
        meta,
        tx_date,
        config.flag,
        payee,
        narration,
        frozenset(tags),
        beancount.core.data.EMPTY_SET,
        postings,
    )


def _sorted_postings(
    postings: list[beancount.core.data.Posting],
) -> list[beancount.core.data.Posting]:
    return sorted(postings, key=lambda posting: posting.units.number)


def _posting(
    account: str, units: Decimal, config: CloverLeafConfig
) -> beancount.core.data.Posting:
    return beancount.core.data.Posting(
        account,
        beancount.core.amount.Amount(units, config.currency),
        None,
        None,
        None,
        None,
    )


def _negate(value: Decimal) -> Decimal:
    negated = -value
    if negated == 0:
        return beancount.core.number.D("0")
    return negated


def _extract_amounts(line: str) -> list[str]:
    cleaned = line.replace("$", "")
    return re.findall(r"\(?-?[\d,]+\.\d{2}\)?", cleaned)


def _parse_amount(amount_str: str) -> Decimal:
    cleaned = amount_str.replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    return beancount.core.number.D(cleaned)


def _render_entries(
    entries: list[beancount.core.data.Directive],
    config: Optional[CloverLeafConfig] = None,
) -> str:
    if config is None:
        config = CloverLeafConfig()

    lines: list[str] = []
    for entry in entries:
        if lines:
            lines.append("")
        if isinstance(entry, beancount.core.data.Balance):
            lines.append(_render_balance(entry, config))
            continue
        lines.extend(_render_transaction(entry, config))
    return "\n".join(lines) + ("\n" if lines else "")


def _render_transaction(
    entry: beancount.core.data.Transaction, config: CloverLeafConfig
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


def _render_balance(
    entry: beancount.core.data.Balance, config: CloverLeafConfig
) -> str:
    amount_str = _format_amount(entry.amount.number)
    prefix = f"{entry.date.isoformat()} balance {entry.account}"
    return _format_balance_line(prefix, amount_str, config.currency)


def _format_balance_line(prefix: str, amount: str, currency: str) -> str:
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


def _parse_statement_period(
    text: str,
) -> Optional[tuple[datetime.date, datetime.date]]:
    match = _PERIOD_RE.search(text)
    if not match:
        return None
    start_date = datetime.datetime.strptime(match.group(1), "%m-%d-%Y").date()
    end_date = datetime.datetime.strptime(match.group(2), "%m-%d-%Y").date()
    return start_date, end_date


def _parse_summary_balances(text: str) -> tuple[Optional[Decimal], Optional[Decimal]]:
    beginning = None
    ending = None
    in_summary = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "SUMMARY":
            in_summary = True
            continue
        if in_summary and line == "TRANSACTION SUMMARY":
            break
        if not in_summary:
            continue
        if line.startswith("Beginning Balance"):
            amounts = _extract_amounts(line)
            if amounts:
                beginning = _parse_amount(amounts[0])
        if line.startswith("Ending Balance"):
            amounts = _extract_amounts(line)
            if amounts:
                ending = _parse_amount(amounts[0])
    return beginning, ending
