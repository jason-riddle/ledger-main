"""Sheer Value Property Management statement parsing and rendering."""

from __future__ import annotations

import dataclasses
import datetime
import re
from decimal import Decimal
from typing import Optional

import beancount.core.amount
import beancount.core.data
import beancount.core.number

import beanout.formatter
import beanout.jsonl


@dataclasses.dataclass(frozen=True)
class SheerValueConfig:
    """Default accounts and settings for Sheer Value parsing."""

    account_property_management: str = "Assets:Property-Management:SheerValue-PM"
    account_owner_distribution: str = "Equity:Owner-Distributions:Owner-Draw"
    payee_management: str = "Sheer Value Property Management"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "imported")


_DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")
_PERIOD_RE = re.compile(
    r"Statement period\s+(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})"
)

_PROPERTY_MAP = {
    "206 Hoover Avenue": ("206-Hoover-Ave", "206 Hoover Avenue"),
    "2943 Butterfly Palm": ("2943-Butterfly-Palm", "2943 Butterfly Palm"),
}


def render_sheer_value_text(
    text: str, config: Optional[SheerValueConfig] = None
) -> str:
    """Render Sheer Value statement text into Beancount entries."""
    entries = parse_sheer_value_text(text, config=config)
    return _render_entries(entries, config=config)


def render_sheer_value_file(
    filepath: str, config: Optional[SheerValueConfig] = None
) -> str:
    """Render a *.pdf.txt Sheer Value file into Beancount text."""
    if not filepath.lower().endswith(".pdf.txt"):
        raise ValueError("Input must be a .pdf.txt file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_sheer_value_text(handle.read(), config=config)


def render_sheer_value_text_to_jsonl(
    text: str, config: Optional[SheerValueConfig] = None
) -> str:
    """Render Sheer Value statement text into JSONL format."""
    entries = parse_sheer_value_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_sheer_value_file_to_jsonl(
    filepath: str, config: Optional[SheerValueConfig] = None
) -> str:
    """Render a *.pdf.txt Sheer Value file into JSONL format."""
    if not filepath.lower().endswith(".pdf.txt"):
        raise ValueError("Input must be a .pdf.txt file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_sheer_value_text_to_jsonl(handle.read(), config=config)


def parse_sheer_value_text(
    text: str, config: Optional[SheerValueConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse Sheer Value statement text into Beancount directives."""
    if config is None:
        config = SheerValueConfig()

    period = _parse_statement_period(text)
    beginning_balance, ending_balance = _parse_balances(text)

    entries: list[beancount.core.data.Directive] = []
    if period and beginning_balance is not None:
        entries.append(
            _build_balance(
                period[0], config.account_property_management, beginning_balance, config
            )
        )

    in_details = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        normalized = re.sub(r"\s+", "", line).lower()
        if "detailtransactions" in normalized:
            in_details = True
            continue

        if not in_details:
            continue

        if "total from subtractions from cash" in line.lower():
            break

        stripped = line.strip()
        if not _DATE_RE.match(stripped):
            continue

        entry = _parse_transaction_line(stripped, config)
        if entry is not None:
            entries.append(entry)

    if period and ending_balance is not None:
        entries.append(
            _build_balance(
                period[1], config.account_property_management, ending_balance, config
            )
        )

    return entries


def _parse_statement_period(
    text: str,
) -> Optional[tuple[datetime.date, datetime.date]]:
    match = _PERIOD_RE.search(text)
    if not match:
        return None
    start_date = datetime.datetime.strptime(match.group(1), "%m/%d/%Y").date()
    end_date = datetime.datetime.strptime(match.group(2), "%m/%d/%Y").date()
    return start_date, end_date


def _parse_balances(text: str) -> tuple[Optional[Decimal], Optional[Decimal]]:
    beginning = None
    ending = None
    in_summary = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = re.sub(r"\s+", "", line).lower()
        if "summarybyproperty" in normalized:
            in_summary = True
            continue
        if in_summary and "incomestatement" in normalized:
            break
        if not in_summary:
            continue
        if line.startswith("Beginning cash balance"):
            amounts = _extract_amounts(line)
            if amounts:
                beginning = _parse_amount(amounts[-1])
        if line.startswith("Ending cash balance"):
            amounts = _extract_amounts(line)
            if amounts:
                ending = _parse_amount(amounts[-1])
    return beginning, ending


def _parse_transaction_line(
    line: str, config: SheerValueConfig
) -> Optional[beancount.core.data.Transaction]:
    columns = re.split(r"\s{2,}", line.strip())
    if len(columns) < 4:
        return None

    if len(columns) < 3 or not _is_amount(columns[-1]) or not _is_amount(columns[-2]):
        return None

    amount = _parse_amount(columns[-2])
    rest = columns[:-2]
    if len(rest) < 4:
        return None

    date_prop = rest[0]
    match = re.match(r"(\d{1,2}/\d{1,2}/\d{4})\s+(.*)", date_prop)
    if not match:
        return None

    tx_date = datetime.datetime.strptime(match.group(1), "%m/%d/%Y").date()
    property_display = match.group(2).strip()
    if property_display not in _PROPERTY_MAP:
        return None

    property_slug, property_label = _PROPERTY_MAP[property_display]
    if len(rest) >= 5:
        account = rest[2]
        name = rest[3]
        memo = rest[4] if len(rest) > 4 else ""
    elif len(rest) == 4 and rest[1].isdigit():
        account = rest[2]
        name = rest[3]
        memo = ""
    else:
        account = rest[1]
        name = rest[2]
        memo = rest[3] if len(rest) > 3 else ""

    if account == "Management":
        account = "Management Fees"

    if account == "Management Fees":
        if name == "Sheer Value Property":
            name = config.payee_management
        if name == "Unit 1 - Sheer Value":
            name = "Unit 1 - Sheer Value Property Management"

    if account == "Cleaning and":
        account = "Cleaning and Maintenance"

    if account == "Owner":
        account = "Owner Contribution"

    if account in {"Rent Income", "Pet Rent", "Late Fee", "Security Deposit"}:
        tenant = None
        if name.startswith("Unit 1 - "):
            tenant = name.replace("Unit 1 - ", "", 1)
        if " by " in name:
            payee = name
        elif memo.lower().startswith("by "):
            payee = f"{name} {memo}"
        elif tenant:
            payee = f"{name} by {tenant}"
        else:
            payee = name
    else:
        payee = name

    reversed_tx = "REVERSED" in memo.upper()

    return _build_transaction(
        tx_date,
        property_slug,
        property_label,
        account,
        payee,
        amount,
        reversed_tx,
        config,
    )


def _build_transaction(
    tx_date: datetime.date,
    property_slug: str,
    property_label: str,
    account: str,
    payee: str,
    amount: Decimal,
    reversed_tx: bool,
    config: SheerValueConfig,
) -> Optional[beancount.core.data.Transaction]:
    meta = beancount.core.data.new_metadata("beanout", 0)

    tags = set(config.tags)
    tags.add(property_slug.lower())
    if reversed_tx:
        tags.add("reversed")

    memo = f"Memo: {property_label} - {account}"
    if reversed_tx:
        memo = f"{memo} - REVERSED"

    if account == "Rent Income":
        income_account = f"Income:Rent:{property_slug}"
        postings = [
            _posting(income_account, _negate(amount), config),
            _posting(config.account_property_management, amount, config),
        ]
    elif account == "Pet Rent":
        income_account = f"Income:Pet-Fee:{property_slug}"
        postings = [
            _posting(income_account, _negate(amount), config),
            _posting(config.account_property_management, amount, config),
        ]
    elif account == "Late Fee":
        income_account = f"Income:Late-Rent-Fee:{property_slug}"
        postings = [
            _posting(income_account, _negate(amount), config),
            _posting(config.account_property_management, amount, config),
        ]
    elif account == "Management Fees":
        expense_account = f"Expenses:Management-Fees:{property_slug}"
        postings = [
            _posting(config.account_property_management, _negate(amount), config),
            _posting(expense_account, amount, config),
        ]
    elif account == "Owner Draw":
        tags.add("distributions")
        postings = [
            _posting(config.account_property_management, _negate(amount), config),
            _posting(config.account_owner_distribution, amount, config),
        ]
    elif account == "Owner Contribution":
        equity_account = "Equity:Owner-Contributions:Cash-Infusion"
        postings = [
            _posting(equity_account, _negate(amount), config),
            _posting(config.account_property_management, amount, config),
        ]
    elif account == "Repairs":
        expense_account = f"Expenses:Repairs:{property_slug}"
        postings = [
            _posting(config.account_property_management, _negate(amount), config),
            _posting(expense_account, amount, config),
        ]
    elif account in {"Cleaning and Maintenance", "Landscaping"}:
        expense_account = f"Expenses:Cleaning---Maintenance:{property_slug}"
        postings = [
            _posting(config.account_property_management, _negate(amount), config),
            _posting(expense_account, amount, config),
        ]
    elif account == "Security Deposit":
        liability_account = f"Liabilities:Security-Deposits-Owed:{property_slug}"
        postings = [
            _posting(liability_account, _negate(amount), config),
            _posting(config.account_property_management, amount, config),
        ]
    else:
        return None

    postings = _sorted_postings(postings)
    return beancount.core.data.Transaction(
        meta,
        tx_date,
        config.flag,
        payee,
        memo,
        frozenset(tags),
        beancount.core.data.EMPTY_SET,
        postings,
    )


def _build_balance(
    tx_date: datetime.date,
    account: str,
    amount: Decimal,
    config: SheerValueConfig,
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


def _sorted_postings(
    postings: list[beancount.core.data.Posting],
) -> list[beancount.core.data.Posting]:
    return sorted(postings, key=lambda posting: posting.units.number)


def _posting(
    account: str, units: Decimal, config: SheerValueConfig
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
    cleaned = line.replace(" ", "").replace("$", "")
    return re.findall(r"\(?-?[\d,]+\.\d{2}\)?", cleaned)


def _parse_amount(amount_str: str) -> Decimal:
    cleaned = amount_str.replace(" ", "").replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    return beancount.core.number.D(cleaned)


def _is_amount(value: str) -> bool:
    cleaned = value.replace(" ", "").replace(",", "").replace("(", "").replace(")", "")
    cleaned = cleaned.replace(".", "")
    cleaned = cleaned.replace("$", "")
    return cleaned.isdigit()


def _render_entries(
    entries: list[beancount.core.data.Directive],
    config: Optional[SheerValueConfig] = None,
) -> str:
    if config is None:
        config = SheerValueConfig()

    # Use Beancount's native formatter for consistent output
    return beanout.formatter.format_entries(entries)
