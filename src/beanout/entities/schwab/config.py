"""Schwab bank configuration and settings."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class SchwabConfig:
    """Default accounts and settings for Schwab parsing."""

    account_cash: str = "Assets:Cash---Bank:Schwab-Checking"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Schwab Bank"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "imported", "schwab")
