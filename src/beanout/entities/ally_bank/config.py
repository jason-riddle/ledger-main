"""Ally Bank configuration and settings."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class AllyBankConfig:
    """Default accounts and settings for Ally Bank parsing."""

    account_cash: str = "Assets:Cash---Bank:Ally-Bank"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Ally Bank"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("ally-bank", "beangulp", "imported")
