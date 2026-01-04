from __future__ import annotations

from beanout import ally_bank, chase, schwab


def test_ally_bank_account_line_alignment() -> None:
    line = ally_bank._format_account_line(
        "  Assets:Cash---Bank:Ally-Bank", "0.97", "USD"
    )
    assert line == "  Assets:Cash---Bank:Ally-Bank      0.97 USD"


def test_chase_account_line_alignment() -> None:
    line = chase._format_account_line(
        "  Liabilities:Credit-Cards:Chase-9265", "-15.42", "USD"
    )
    assert line == "  Liabilities:Credit-Cards:Chase-9265    -15.42 USD"


def test_schwab_account_line_alignment() -> None:
    line = schwab._format_account_line(
        "  Equity:Opening-Balances", "-0.21", "USD"
    )
    assert line == "  Equity:Opening-Balances                -0.21 USD"
