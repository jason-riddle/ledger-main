"""Sheer Value Property Management configuration and settings."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class SheerValueConfig:
    """Default accounts and settings for Sheer Value parsing."""

    account_property_management: str = "Assets:Property-Management:SheerValue-PM"
    account_owner_distribution: str = "Equity:Owner-Distributions:Owner-Draw"
    payee_management: str = "Sheer Value Property Management"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "imported")
