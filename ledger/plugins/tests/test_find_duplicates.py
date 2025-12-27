#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "pytest>=7.0.0",
#   "beancount>=3.2.0",
# ]
# ///

"""Unit tests for duplicate-detection plugin."""

import datetime as dt
import logging
from pathlib import Path
import sys

import beancount.core.data as data
from beancount.core.amount import Amount
from beancount.core.number import D

PLUGINS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGINS_DIR))

import find_duplicates  # type: ignore  # noqa: E402


def _txn(date_str, amount, account="Assets:Cash---Bank:Checking"):
    date = dt.date.fromisoformat(date_str)
    units = Amount(D(str(amount)), "USD")
    postings = [
        data.Posting(account, units, None, None, None, None),
        data.Posting("Income:Rent:206-Hoover-Ave", None, None, None, None, None),
    ]
    meta = {"comments": "test"}
    return data.Transaction(meta, date, "*", "Tenant", "Rent", None, None, postings)


def _txn_with_expense(date_str, amount, account="Assets:Cash---Bank:Checking"):
    date = dt.date.fromisoformat(date_str)
    units = Amount(D(str(amount)), "USD")
    postings = [
        data.Posting(account, units, None, None, None, None),
        data.Posting("Expenses:Repairs:206-Hoover-Ave", -units, None, None, None, None),
    ]
    meta = {"comments": "test"}
    return data.Transaction(meta, date, "*", "Vendor", "Repair", None, None, postings)


def test_warns_on_likely_duplicates(caplog):
    txn_a = _txn("2025-01-12", "100.00")
    txn_b = _txn("2025-01-13", "100.00")

    with caplog.at_level(logging.WARNING):
        _, diagnostics = find_duplicates.plugin(
            [txn_a, txn_b],
            {},
            "warn_threshold=0.80 error_threshold=0.95 window=3 tolerance=0.03",
        )

    assert diagnostics == []
    assert any("Duplicate confidence" in record.message for record in caplog.records)


def test_errors_on_high_confidence_duplicates():
    txn_a = _txn("2025-01-12", "100.00")
    txn_b = _txn("2025-01-12", "100.00")

    _, diagnostics = find_duplicates.plugin(
        [txn_a, txn_b],
        {},
        "warn_threshold=0.80 error_threshold=0.95 window=3 tolerance=0.03",
    )

    assert len(diagnostics) == 1
    assert isinstance(diagnostics[0], find_duplicates.DuplicateError)


def test_ignores_amounts_outside_tolerance(caplog):
    txn_a = _txn("2025-01-12", "100.00")
    txn_b = _txn("2025-01-13", "100.05")

    with caplog.at_level(logging.WARNING):
        _, diagnostics = find_duplicates.plugin(
            [txn_a, txn_b],
            {},
            "warn_threshold=0.80 error_threshold=0.95 window=3 tolerance=0.03",
        )

    assert diagnostics == []
    assert caplog.records == []


def test_cash_only_avoids_zero_net_false_positives(caplog):
    txn_a = _txn_with_expense("2025-01-12", "100.00")
    txn_b = _txn_with_expense("2025-01-12", "50.00")

    with caplog.at_level(logging.WARNING):
        _, diagnostics = find_duplicates.plugin(
            [txn_a, txn_b],
            {},
            (
                "warn_threshold=0.80 error_threshold=0.95 window=3 "
                "tolerance=0.03 cash_only=true"
            ),
        )

    assert diagnostics == []
    assert caplog.records == []


def test_property_match_blocks_different_properties(caplog):
    txn_a = _txn_with_expense("2025-01-12", "117.00")
    txn_b = _txn_with_expense("2025-01-12", "117.00")
    txn_b = txn_b._replace(
        postings=[
            txn_b.postings[0],
            data.Posting(
                "Expenses:Management-Fees:2943-Butterfly-Palm",
                -txn_b.postings[0].units,
                None,
                None,
                None,
                None,
            ),
        ]
    )

    with caplog.at_level(logging.WARNING):
        _, diagnostics = find_duplicates.plugin(
            [txn_a, txn_b],
            {},
            (
                "warn_threshold=0.80 error_threshold=0.95 window=3 "
                "tolerance=0.03 cash_only=true property_match=true"
            ),
        )

    assert diagnostics == []
    assert caplog.records == []


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
