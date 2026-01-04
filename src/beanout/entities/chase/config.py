"""Chase credit card configuration and settings."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class ChaseConfig:
    """Default accounts and settings for Chase parsing."""

    account_credit: str = "Liabilities:Credit-Cards:Chase-9265"
    account_offset: str = "Equity:Opening-Balances"
    payee: str = "Chase"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = ("beangulp", "chase", "imported")
