"""Amount parsing utilities for Beancount parsers.

This module provides shared utilities for parsing monetary amounts from
various text formats into Decimal values suitable for Beancount.
"""

from decimal import Decimal

import beancount.core.number


def parse_amount(amount_str: str) -> Decimal:
    """Parse an amount string into a Decimal.

    Handles common amount formats:
    - Dollar signs: "$1,234.56"
    - Commas: "1,234.56"
    - Parentheses for negatives: "(65.47)" -> -65.47
    - Empty strings: "" -> 0

    Args:
        amount_str: A string amount (e.g. "$1,234.56", "(65.47)").

    Returns:
        Decimal instance of the parsed amount.
    """
    if not amount_str or amount_str.strip() == "":
        return beancount.core.number.D("0")

    cleaned = amount_str.strip().replace("$", "").replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    return beancount.core.number.D(cleaned)


def parse_optional_amount(value: str | None) -> Decimal:
    """Parse an optional amount string into a Decimal.

    Args:
        value: Optional string amount or None.

    Returns:
        Decimal instance of the parsed amount, or zero if None/empty.
    """
    if value is None:
        return beancount.core.number.D("0")
    cleaned = str(value).strip()
    if not cleaned or cleaned == "$0.00":
        return beancount.core.number.D("0")
    return parse_amount(cleaned)


def ensure_decimal(value: Decimal) -> Decimal:
    """Ensure a value is a Decimal, converting if necessary.

    Args:
        value: A value that might be a Decimal or convertible to one.

    Returns:
        Decimal instance.
    """
    if isinstance(value, Decimal):
        return value
    return beancount.core.number.D(str(value))


def negate(value: Decimal) -> Decimal:
    """Negate a Decimal and normalize negative zero.

    Args:
        value: Decimal to negate.

    Returns:
        Negated Decimal, with -0 normalized to 0.
    """
    negated = -value
    if negated == 0:
        return beancount.core.number.D("0")
    return negated
