"""Tests for shared common utilities."""

import datetime
from decimal import Decimal

from beanout.common import amounts, beancount_helpers


def test_parse_amount():
    """Test amount parsing from various formats."""
    assert amounts.parse_amount("$1,234.56") == Decimal("1234.56")
    assert amounts.parse_amount("(65.47)") == Decimal("-65.47")
    assert amounts.parse_amount("") == Decimal("0")
    assert amounts.parse_amount("100.00") == Decimal("100.00")


def test_parse_optional_amount():
    """Test optional amount parsing."""
    assert amounts.parse_optional_amount(None) == Decimal("0")
    assert amounts.parse_optional_amount("") == Decimal("0")
    assert amounts.parse_optional_amount("$0.00") == Decimal("0")
    assert amounts.parse_optional_amount("123.45") == Decimal("123.45")


def test_negate():
    """Test negation with zero normalization."""
    assert amounts.negate(Decimal("10")) == Decimal("-10")
    assert amounts.negate(Decimal("-10")) == Decimal("10")
    # Negative zero should normalize to zero
    result = amounts.negate(Decimal("0"))
    assert result == Decimal("0")
    assert str(result) == "0"


def test_sort_postings():
    """Test posting sorting (negative before positive)."""
    posting1 = beancount_helpers.create_posting("Assets:Test", Decimal("100"), "USD")
    posting2 = beancount_helpers.create_posting("Expenses:Test", Decimal("-100"), "USD")

    sorted_postings = beancount_helpers.sort_postings([posting1, posting2])

    # Negative should come first
    assert sorted_postings[0].units.number == Decimal("-100")
    assert sorted_postings[1].units.number == Decimal("100")


def test_create_transaction():
    """Test transaction creation."""
    posting1 = beancount_helpers.create_posting("Assets:Cash", Decimal("-100"), "USD")
    posting2 = beancount_helpers.create_posting("Expenses:Food", Decimal("100"), "USD")

    txn = beancount_helpers.create_transaction(
        date=datetime.date(2024, 1, 1),
        flag="*",
        payee="Test Store",
        narration="Test purchase",
        postings=[posting1, posting2],
        tags={"test"},
    )

    assert txn.date == datetime.date(2024, 1, 1)
    assert txn.flag == "*"
    assert txn.payee == "Test Store"
    assert txn.narration == "Test purchase"
    assert "test" in txn.tags
    assert len(txn.postings) == 2


if __name__ == "__main__":
    test_parse_amount()
    test_parse_optional_amount()
    test_negate()
    test_sort_postings()
    test_create_transaction()
    print("✅ All common utility tests passed!")
