"""Beancount-specific helper utilities for creating directives.

This module provides shared utilities for constructing Beancount
directives such as Transactions, Postings, and Balances.
"""

from __future__ import annotations

import datetime
from decimal import Decimal

import beancount.core.amount
import beancount.core.data


def create_posting(
    account: str,
    amount: Decimal,
    currency: str,
) -> beancount.core.data.Posting:
    """Create a Beancount Posting.

    Args:
        account: Account name.
        amount: Amount as Decimal.
        currency: Currency code (e.g., "USD").

    Returns:
        Beancount Posting directive.
    """
    return beancount.core.data.Posting(
        account,
        beancount.core.amount.Amount(amount, currency),
        None,
        None,
        None,
        None,
    )


def create_transaction(
    date: datetime.date,
    flag: str,
    payee: str,
    narration: str,
    postings: list[beancount.core.data.Posting],
    tags: set[str] | frozenset[str] | None = None,
    links: set[str] | frozenset[str] | None = None,
    meta: dict | None = None,
) -> beancount.core.data.Transaction:
    """Create a Beancount Transaction.

    Args:
        date: Transaction date.
        flag: Transaction flag (e.g., "*" or "!").
        payee: Payee name.
        narration: Transaction description.
        postings: List of postings.
        tags: Optional set of tags.
        links: Optional set of links.
        meta: Optional metadata dict.

    Returns:
        Beancount Transaction directive.
    """
    if meta is None:
        meta = {}
    if tags is None:
        tags = set()
    if links is None:
        links = set()

    return beancount.core.data.Transaction(
        meta,
        date,
        flag,
        payee,
        narration,
        frozenset(tags) if not isinstance(tags, frozenset) else tags,
        frozenset(links) if not isinstance(links, frozenset) else links,
        postings,
    )


def create_balance(
    date: datetime.date,
    account: str,
    amount: Decimal,
    currency: str,
    meta: dict | None = None,
) -> beancount.core.data.Balance:
    """Create a Beancount Balance directive.

    Args:
        date: Balance assertion date.
        account: Account name.
        amount: Expected balance as Decimal.
        currency: Currency code (e.g., "USD").
        meta: Optional metadata dict.

    Returns:
        Beancount Balance directive.
    """
    if meta is None:
        meta = beancount.core.data.new_metadata("beanout", 0)
    return beancount.core.data.Balance(
        meta,
        date,
        account,
        beancount.core.amount.Amount(amount, currency),
        None,
        None,
    )


def sort_postings(
    postings: list[beancount.core.data.Posting],
) -> list[beancount.core.data.Posting]:
    """Sort postings by amount (negative first, then positive).

    This follows the convention in the repository of listing
    negative postings first, then positive postings.

    Args:
        postings: List of postings to sort.

    Returns:
        Sorted list of postings.
    """
    return sorted(postings, key=lambda posting: posting.units.number)


def build_two_posting_transaction(
    date: datetime.date,
    flag: str,
    payee: str,
    narration: str,
    account1: str,
    amount1: Decimal,
    account2: str,
    amount2: Decimal,
    currency: str,
    tags: set[str] | frozenset[str] | None = None,
    links: set[str] | frozenset[str] | None = None,
    meta: dict | None = None,
) -> beancount.core.data.Transaction:
    """Create a transaction with exactly two postings.

    This is a convenience function for the common case of a simple
    two-account transaction. Postings are automatically sorted.

    Args:
        date: Transaction date.
        flag: Transaction flag.
        payee: Payee name.
        narration: Transaction description.
        account1: First account.
        amount1: Amount for first account.
        account2: Second account.
        amount2: Amount for second account.
        currency: Currency code.
        tags: Optional set of tags.
        links: Optional set of links.
        meta: Optional metadata dict.

    Returns:
        Beancount Transaction directive.
    """
    postings = [
        create_posting(account1, amount1, currency),
        create_posting(account2, amount2, currency),
    ]
    postings = sort_postings(postings)
    return create_transaction(date, flag, payee, narration, postings, tags, links, meta)
