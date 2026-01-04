"""Fidelity brokerage configuration and settings."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class FidelityConfig:
    """Default accounts and settings for Fidelity parsing."""

    account_cash: str = "Assets:Investments:Fidelity:Cash"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Fidelity"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "imported", "fidelity")
