"""CloverLeaf Property Management statement parsing and rendering."""

from __future__ import annotations

import csv
import dataclasses
import datetime
import io
import json
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


def render_clover_leaf_csv_text(
    text: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render CloverLeaf CSV ledger content into Beancount entries."""
    entries = parse_clover_leaf_csv_text(text, config=config)
    return _render_entries(entries, config=config)


def render_clover_leaf_json_text(
    text: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render CloverLeaf JSON ledger content into Beancount entries."""
    entries = parse_clover_leaf_json_text(text, config=config)
    return _render_entries(entries, config=config)


def render_clover_leaf_file(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.pdf.txt CloverLeaf file into Beancount text."""
    if not filepath.lower().endswith(".pdf.txt"):
        raise ValueError("Input must be a .pdf.txt file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_text(handle.read(), config=config)


def render_clover_leaf_csv_file(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.csv CloverLeaf file into Beancount text."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_csv_text(handle.read(), config=config)


def render_clover_leaf_json_file(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.json CloverLeaf file into Beancount text."""
    if not filepath.lower().endswith(".json"):
        raise ValueError("Input must be a .json file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_json_text(handle.read(), config=config)


def render_clover_leaf_text_to_jsonl(
    text: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render CloverLeaf statement text into JSONL format."""
    entries = parse_clover_leaf_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_clover_leaf_csv_text_to_jsonl(
    text: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render CloverLeaf CSV ledger content into JSONL format."""
    entries = parse_clover_leaf_csv_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_clover_leaf_json_text_to_jsonl(
    text: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render CloverLeaf JSON ledger content into JSONL format."""
    entries = parse_clover_leaf_json_text(text, config=config)
    return beanout.jsonl.directives_to_jsonl(entries)


def render_clover_leaf_file_to_jsonl(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.pdf.txt CloverLeaf file into JSONL format."""
    if not filepath.lower().endswith(".pdf.txt"):
        raise ValueError("Input must be a .pdf.txt file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_text_to_jsonl(handle.read(), config=config)


def render_clover_leaf_csv_file_to_jsonl(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.csv CloverLeaf file into JSONL format."""
    if not filepath.lower().endswith(".csv"):
        raise ValueError("Input must be a .csv file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_csv_text_to_jsonl(handle.read(), config=config)


def render_clover_leaf_json_file_to_jsonl(
    filepath: str, config: Optional[CloverLeafConfig] = None
) -> str:
    """Render a *.json CloverLeaf file into JSONL format."""
    if not filepath.lower().endswith(".json"):
        raise ValueError("Input must be a .json file")
    with open(filepath, "r", encoding="utf-8") as handle:
        return render_clover_leaf_json_text_to_jsonl(handle.read(), config=config)


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


def parse_clover_leaf_csv_text(
    text: str, config: Optional[CloverLeafConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse CloverLeaf CSV ledger content into Beancount directives."""
    if config is None:
        config = CloverLeafConfig()

    entries: list[beancount.core.data.Directive] = []
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if row]
    if not rows:
        return entries

    header_index = None
    for idx, row in enumerate(rows):
        header = [col.strip().lower() for col in row]
        if header[:8] == [
            "date posted",
            "account",
            "property / unit",
            "reference",
            "description",
            "increase",
            "decrease",
            "balance",
        ]:
            header_index = idx
            break

    if header_index is None:
        raise ValueError("Unexpected CloverLeaf CSV header")

    for row in rows[header_index + 1 :]:
        if len(row) < 8:
            continue
        (
            date_raw,
            account_raw,
            property_raw,
            _,
            description,
            increase_raw,
            decrease_raw,
            _,
        ) = [col.strip() for col in row[:8]]
        if not date_raw:
            continue
        try:
            tx_date = datetime.datetime.strptime(date_raw, "%m-%d-%Y").date()
        except ValueError:
            continue

        increase = _parse_optional_amount(increase_raw)
        decrease = _parse_optional_amount(decrease_raw)
        net_amount = increase - decrease
        if net_amount == 0:
            continue

        account_number, account_name = _split_account(account_raw)
        property_name = _infer_property_name(property_raw)
        tags = _build_tags(property_name, config)

        mapped = _map_ledger_account(
            account_number, account_name, description, property_name, config
        )
        if mapped is None:
            continue
        account, payee, is_owner_distribution = mapped

        if is_owner_distribution:
            entries.append(
                _build_owner_distribution(tx_date, payee, net_amount, config)
            )
            continue

        entries.append(
            _build_transaction(
                tx_date,
                payee,
                f"Memo: {description}".strip(),
                tags,
                net_amount,
                account,
                config,
            )
        )

    return entries


def parse_clover_leaf_json_text(
    text: str, config: Optional[CloverLeafConfig] = None
) -> list[beancount.core.data.Directive]:
    """Parse CloverLeaf JSON ledger content into Beancount directives."""
    if config is None:
        config = CloverLeafConfig()

    data = json.loads(text)
    rows = data.get("rows", []) or []
    entries: list[beancount.core.data.Directive] = []

    for row in rows:
        if row.get("rowTypeID") != 3:
            continue
        payload = row.get("data") or {}
        date_raw = (payload.get("datePosted") or "").strip()
        if not date_raw:
            continue
        try:
            tx_date = datetime.datetime.strptime(date_raw, "%Y-%m-%d").date()
        except ValueError:
            continue

        increase = _parse_optional_amount(payload.get("increase"))
        decrease = _parse_optional_amount(payload.get("decrease"))
        net_amount = increase - decrease
        if net_amount == 0:
            continue

        account_number = (payload.get("accountNumber") or "").strip()
        account_name = (payload.get("accountName") or "").strip()
        description = (payload.get("description") or "").strip()
        payee = (payload.get("payeePayerName") or "").strip()
        property_name = _infer_property_name(
            payload.get("propertyAddress") or payload.get("unitAddress") or ""
        )
        tags = _build_tags(property_name, config)

        mapped = _map_ledger_account(
            account_number, account_name, description, property_name, config
        )
        if mapped is None:
            continue
        account, mapped_payee, is_owner_distribution = mapped
        if not payee:
            payee = mapped_payee

        if is_owner_distribution:
            entries.append(
                _build_owner_distribution(tx_date, payee, net_amount, config)
            )
            continue

        entries.append(
            _build_transaction(
                tx_date,
                payee,
                f"Memo: {description}".strip(),
                tags,
                net_amount,
                account,
                config,
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


def _parse_optional_amount(value: Optional[str]) -> Decimal:
    if value is None:
        return beancount.core.number.D("0")
    cleaned = str(value).strip()
    if not cleaned or cleaned == "$0.00":
        return beancount.core.number.D("0")
    return _parse_amount(cleaned)


def _split_account(raw: str) -> tuple[str, str]:
    if ":" in raw:
        number, name = raw.split(":", 1)
        return number.strip(), name.strip()
    return "", raw.strip()


def _infer_property_name(raw: str) -> Optional[str]:
    lowered = raw.lower()
    if "2943" in lowered and "butterfly" in lowered:
        return "2943-Butterfly-Palm"
    if "206" in lowered and "hoover" in lowered:
        return "206-Hoover-Ave"
    return None


def _build_tags(property_name: Optional[str], config: CloverLeafConfig) -> set[str]:
    tags = set(config.tags)
    if property_name:
        tag = _PROPERTY_TAGS.get(property_name)
        if tag:
            tags.add(tag)
    return tags


def _map_ledger_account(
    account_number: str,
    account_name: str,
    description: str,
    property_name: Optional[str],
    config: CloverLeafConfig,
) -> Optional[tuple[str, str, bool]]:
    account_number = account_number.strip()
    account_name_upper = account_name.upper()
    desc_upper = description.upper()

    if account_number == "3250" or "OWNER DISTRIBUTION" in account_name_upper:
        return config.account_owner_distribution, "Owner", True

    if not property_name:
        return None

    if account_number == "4100" or account_name_upper == "RENT":
        return f"Income:Rent:{property_name}", config.payee_tenant, False

    if account_number == "6100" or "MANAGEMENT FEE" in account_name_upper:
        return (
            f"Expenses:Management-Fees:{property_name}",
            config.payee_management,
            False,
        )

    if account_number == "6415" or "UTILITIES" in account_name_upper:
        if "WATER" in desc_upper:
            return (
                f"Expenses:Utilities:Water:{property_name}",
                config.payee_management,
                False,
            )
        return (
            f"Expenses:Utilities:Electric:{property_name}",
            config.payee_management,
            False,
        )

    if account_number == "6404" or "LANDSCAP" in account_name_upper:
        return (
            f"Expenses:Cleaning---Maintenance:{property_name}",
            config.payee_contractor,
            False,
        )

    if account_number == "6403" or "GENERAL REPAIRS" in account_name_upper:
        return f"Expenses:Repairs:{property_name}", config.payee_contractor, False

    if account_number == "6405" or "LOCK CHANGE" in account_name_upper:
        return f"Expenses:Repairs:{property_name}", config.payee_contractor, False

    if account_number == "6420" or "PAINT" in account_name_upper:
        return f"Expenses:Repairs:{property_name}", config.payee_contractor, False

    if account_number == "6430" or "MAID CLEAN" in account_name_upper:
        return (
            f"Expenses:Cleaning---Maintenance:{property_name}",
            config.payee_contractor,
            False,
        )

    if account_number == "6450" or "INSPECTION" in account_name_upper:
        return f"Expenses:Repairs:{property_name}", config.payee_contractor, False

    if account_number == "6460" or account_number == "6461":
        return f"Expenses:Repairs:{property_name}", config.payee_contractor, False

    return f"Expenses:Unidentified:{property_name}", config.payee_management, False


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
    payee = _sanitize_text(payee)
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
    payee = _sanitize_text(payee)
    narration = _sanitize_text(narration)
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


def _sanitize_text(value: str) -> str:
    return value.replace("\r\n", " ").replace("\n", " ").replace("\t", " ").strip()


def _extract_amounts(line: str) -> list[str]:
    cleaned = line.replace("$", "")
    return re.findall(r"\(?-?[\d,]+\.\d{2}\)?", cleaned)


def _parse_amount(amount_str: str) -> Decimal:
    cleaned = amount_str.replace("$", "").replace(",", "")
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
