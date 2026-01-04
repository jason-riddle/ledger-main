"""SPS Mortgage Servicing statement parsing and rendering."""

import dataclasses
import datetime
import re
from decimal import Decimal
from typing import Optional

import beancount.core.data

from beanout.common import amounts, beancount_helpers, io, rendering


@dataclasses.dataclass(frozen=True)
class SPSConfig:
    """Default accounts and settings for SPS parsing."""

    account_mortgage: str = "Liabilities:Mortgages:2943-Butterfly-Palm"
    account_interest: str = "Expenses:Mortgage-Interest:2943-Butterfly-Palm"
    account_escrow: str = "Assets:Escrow:Taxes---Insurance:2943-Butterfly-Palm"
    account_equity: str = "Equity:Owner-Contributions:Cash-Infusion"
    account_insurance: str = "Expenses:Insurance:2943-Butterfly-Palm"
    account_property_taxes: str = "Expenses:Property-Taxes:2943-Butterfly-Palm"
    payee: str = "SPS Mortgage Servicing"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = (
        "2943-butterfly-palm",
        "beangulp",
        "imported",
        "mortgage",
    )


_STATEMENT_DATE_RE = re.compile(r"Statement Date:(\d{2}/\d{2}/\d{4})")
_PERIOD_RE = re.compile(
    r"Transaction Activity \((\d{2}/\d{2}/\d{4}) to "
    r"(\d{2}/\d{2}/\d{4})\)"
)


def render_sps_text(text: str, config: Optional[SPSConfig] = None) -> str:
    """Render SPS statement text into Beancount entries.

    Args:
        text: Full text extracted from an SPS PDF.
        config: Optional SPSConfig for account defaults.

    Returns:
        Beancount-formatted text.
    """
    entries = parse_sps_text(text, config=config)
    return rendering.render_to_beancount(entries)


def render_sps_file(filepath: str, config: Optional[SPSConfig] = None) -> str:
    """Render a *.pdf.txt SPS file into Beancount text.

    Args:
        filepath: Path to the SPS PDF text file.
        config: Optional SPSConfig for account defaults.

    Returns:
        Beancount-formatted text.
    """
    return io.render_file_generic(
        filepath,
        ".pdf.txt",
        lambda text: render_sps_text(text, config),
    )


def render_sps_text_to_jsonl(text: str, config: Optional[SPSConfig] = None) -> str:
    """Render SPS statement text into JSONL format.

    Args:
        text: Full text extracted from an SPS PDF.
        config: Optional SPSConfig for account defaults.

    Returns:
        JSONL-formatted text.
    """
    entries = parse_sps_text(text, config=config)
    return rendering.render_to_jsonl(entries)


def render_sps_file_to_jsonl(filepath: str, config: Optional[SPSConfig] = None) -> str:
    """Render a *.pdf.txt SPS file into JSONL format.

    Args:
        filepath: Path to the SPS PDF text file.
        config: Optional SPSConfig for account defaults.

    Returns:
        JSONL-formatted text.
    """
    return io.render_file_generic(
        filepath,
        ".pdf.txt",
        lambda text: render_sps_text_to_jsonl(text, config),
    )


def parse_sps_text(
    text: str, config: Optional[SPSConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse SPS statement text into Beancount directives.

    Args:
        text: Full text extracted from an SPS PDF.
        config: Optional SPSConfig for account defaults.

    Returns:
        List of Beancount directives.
    """
    if config is None:
        config = SPSConfig()

    statement_date = _parse_statement_date(text)
    period = _parse_statement_period(text)

    opening_balances = None
    closing_balances = None
    transactions: list[beancount.core.data.Directive] = []

    for tx_data in _parse_transactions(text, statement_date):
        desc, _, principal, interest, escrow, _, _, total = tx_data
        desc_upper = desc.upper()

        if "BEG BALANCE" in desc_upper:
            opening_balances = _balances_from_amounts(
                period[0], principal, interest, escrow, config
            )
            continue
        if "ENDING BALANCE" in desc_upper:
            closing_balances = _balances_from_amounts(
                period[1], principal, interest, escrow, config
            )
            continue

        transaction = _build_transaction(
            desc, tx_data[1], principal, interest, escrow, total, config
        )
        if transaction is not None:
            transactions.append(transaction)

    entries: list[beancount.core.data.Directive] = []
    if opening_balances:
        entries.extend(opening_balances)
    entries.extend(transactions)
    if closing_balances:
        entries.extend(closing_balances)

    return entries


def _parse_statement_date(text: str) -> datetime.date:
    """Extract the statement date from SPS text."""
    match = _STATEMENT_DATE_RE.search(text)
    if not match:
        raise ValueError("Statement Date not found in SPS text")
    return datetime.datetime.strptime(match.group(1), "%m/%d/%Y").date()


def _parse_statement_period(text: str) -> tuple[datetime.date, datetime.date]:
    """Extract the statement period from SPS text."""
    match = _PERIOD_RE.search(text)
    if not match:
        raise ValueError("Statement period not found in SPS text")
    start_date = datetime.datetime.strptime(match.group(1), "%m/%d/%Y").date()
    end_date = datetime.datetime.strptime(match.group(2), "%m/%d/%Y").date()
    return start_date, end_date


def _parse_transactions(
    text: str, statement_date: datetime.date
) -> list[
    tuple[str, datetime.date, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]
]:
    """Parse transaction rows from the statement text."""
    entries: list[
        tuple[
            str,
            datetime.date,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
        ]
    ] = []

    in_section = False
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if not in_section:
            if "Transaction Activity" in line:
                in_section = True
            continue

        if "Past Payments Breakdown" in line:
            if current_lines:
                _append_transaction_from_lines(current_lines, statement_date, entries)
            break

        if re.match(r"^\d{2}/\d{2}\b", line):
            if current_lines:
                _append_transaction_from_lines(current_lines, statement_date, entries)
            current_lines = [line]
            continue

        if current_lines:
            current_lines.append(line)

    if in_section and current_lines:
        _append_transaction_from_lines(current_lines, statement_date, entries)

    return entries


def _append_transaction_from_lines(
    lines: list[str],
    statement_date: datetime.date,
    entries: list[
        tuple[
            str,
            datetime.date,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
            Decimal,
        ]
    ],
) -> None:
    """Parse a buffered transaction line and append to entries."""
    combined = " ".join(lines)
    combined = combined.replace(", ", ",")

    parsed = _parse_transaction_line(combined, statement_date)
    if parsed is not None:
        entries.append(parsed)


def _parse_transaction_line(
    line: str, statement_date: datetime.date
) -> Optional[
    tuple[str, datetime.date, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]
]:
    """Parse a single transaction row."""
    match = re.match(
        r"^\s*(\d{2}/\d{2})\s+(.+?)\s+([^\s]+)\s+([^\s]+)\s+"
        r"([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s*$",
        line,
    )
    if not match:
        return None

    date_str = match.group(1)
    desc = match.group(2).strip()
    principal_str = match.group(3)
    interest_str = match.group(4)
    escrow_str = match.group(5)
    late_str = match.group(6)
    other_str = match.group(7)
    total_str = match.group(8)

    if not _is_numeric_amount(principal_str):
        return None

    tx_date = datetime.datetime.strptime(
        f"{date_str}/{statement_date.year}", "%m/%d/%Y"
    ).date()

    return (
        desc,
        tx_date,
        amounts.parse_amount(principal_str),
        amounts.parse_amount(interest_str),
        amounts.parse_amount(escrow_str),
        amounts.parse_amount(late_str),
        amounts.parse_amount(other_str),
        amounts.parse_amount(total_str),
    )


def _is_numeric_amount(value: str) -> bool:
    """Return True if the value looks like a numeric amount."""
    cleaned = value.replace("-", "")
    cleaned = cleaned.replace(",", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = cleaned.replace(".", "")
    cleaned = cleaned.replace("$", "")
    return cleaned.isdigit()


def _balances_from_amounts(
    balance_date: datetime.date,
    principal: Decimal,
    interest: Decimal,
    escrow: Decimal,
    config: SPSConfig,
) -> list[beancount.core.data.Balance]:
    """Create balance directives for mortgage, escrow, and interest."""
    return [
        beancount_helpers.create_balance(
            balance_date,
            config.account_escrow,
            amounts.negate(escrow),
            config.currency,
        ),
        beancount_helpers.create_balance(
            balance_date,
            config.account_mortgage,
            amounts.negate(principal),
            config.currency,
        ),
        beancount_helpers.create_balance(
            balance_date,
            config.account_interest,
            amounts.negate(interest),
            config.currency,
        ),
    ]


def _build_transaction(
    desc: str,
    tx_date: datetime.date,
    principal: Decimal,
    interest: Decimal,
    escrow: Decimal,
    total: Decimal,
    config: SPSConfig,
) -> Optional[beancount.core.data.Transaction]:
    """Build a transaction directive for a parsed row."""
    desc_upper = re.sub(r"\s+", " ", desc.upper()).strip()

    if "HAZARD" in desc_upper and "INS" in desc_upper:
        memo = "Memo: Hazard Insurance"
        escrow_units = amounts.negate(escrow)
        expense_units = amounts.negate(escrow_units)
        postings = [
            beancount_helpers.create_posting(config.account_escrow, escrow_units, config.currency),
            beancount_helpers.create_posting(config.account_insurance, expense_units, config.currency),
        ]
    elif "COUNTY TAX" in desc_upper:
        memo = "Memo: County Tax"
        escrow_units = amounts.negate(escrow)
        expense_units = amounts.negate(escrow_units)
        postings = [
            beancount_helpers.create_posting(config.account_escrow, escrow_units, config.currency),
            beancount_helpers.create_posting(config.account_property_taxes, expense_units, config.currency),
        ]
    elif "SPECIAL DEPOSIT" in desc_upper:
        memo = "Memo: Special Deposit"
        postings = [
            beancount_helpers.create_posting(config.account_equity, total, config.currency),
            beancount_helpers.create_posting(config.account_escrow, amounts.negate(escrow), config.currency),
        ]
    elif "PAYMENT" in desc_upper:
        memo = "Memo: Mortgage"
        postings = [
            beancount_helpers.create_posting(config.account_equity, total, config.currency),
            beancount_helpers.create_posting(config.account_mortgage, amounts.negate(principal), config.currency),
            beancount_helpers.create_posting(config.account_interest, amounts.negate(interest), config.currency),
            beancount_helpers.create_posting(config.account_escrow, amounts.negate(escrow), config.currency),
        ]
    else:
        return None

    return beancount_helpers.create_transaction(
        tx_date,
        config.flag,
        config.payee,
        memo,
        postings,
        tags=set(config.tags),
    )
