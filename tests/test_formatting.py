from __future__ import annotations

import datetime

import beancount.core.amount
import beancount.core.data
import beancount.core.number
from beanout import formatter


def test_format_entries_with_transactions() -> None:
    """Test that format_entries properly formats transactions using Beancount's native formatter."""
    # Create a simple transaction
    meta = beancount.core.data.new_metadata("test", 0)
    date = datetime.date(2025, 1, 1)
    posting1 = beancount.core.data.Posting(
        "Assets:Cash---Bank:Ally-Bank",
        beancount.core.amount.Amount(beancount.core.number.D("100.50"), "USD"),
        None,
        None,
        None,
        None,
    )
    posting2 = beancount.core.data.Posting(
        "Equity:Opening-Balances",
        beancount.core.amount.Amount(beancount.core.number.D("-100.50"), "USD"),
        None,
        None,
        None,
        None,
    )
    txn = beancount.core.data.Transaction(
        meta,
        date,
        "*",
        "Test Payee",
        "Test narration",
        frozenset(["test-tag"]),
        frozenset(),
        [posting1, posting2],
    )

    output = formatter.format_entries([txn])

    # Verify the output contains the expected components
    assert "2025-01-01" in output
    assert "Test Payee" in output
    assert "Test narration" in output
    assert "#test-tag" in output
    assert "Assets:Cash---Bank:Ally-Bank" in output
    assert "Equity:Opening-Balances" in output
    assert "100.50 USD" in output
    assert "-100.50 USD" in output
    # Beancount's formatter should produce properly formatted output
    assert output.endswith("\n")


def test_format_entries_with_balances() -> None:
    """Test that format_entries properly formats balance directives."""
    meta = beancount.core.data.new_metadata("test", 0)
    date = datetime.date(2025, 1, 1)
    balance = beancount.core.data.Balance(
        meta,
        date,
        "Assets:Cash---Bank:Ally-Bank",
        beancount.core.amount.Amount(beancount.core.number.D("1000.00"), "USD"),
        None,
        None,
    )

    output = formatter.format_entries([balance])

    # Verify the output contains the expected components
    assert "2025-01-01" in output
    assert "balance" in output
    assert "Assets:Cash---Bank:Ally-Bank" in output
    assert "1000.00 USD" in output
    assert output.endswith("\n")


def test_format_entries_empty() -> None:
    """Test that format_entries handles empty list."""
    output = formatter.format_entries([])
    assert output == ""


