"""SPS Mortgage Servicing configuration and settings."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class SPSConfig:
    """Default accounts and settings for SPS parsing."""

    account_mortgage: str = "Liabilities:Mortgages:2943-Butterfly-Palm"
    account_interest: str = "Expenses:Mortgage-Interest:2943-Butterfly-Palm"
    account_escrow: str = "Assets:Escrow:Taxes---Insurance:2943-Butterfly-Palm"
    account_equity: str = "Equity:Owner-Contributions:Cash-Infusion"
    account_insurance: str = "Expenses:Insurance:2943-Butterfly-Palm"
    account_property_taxes: str = "Expenses:Property-Taxes:2943-Butterfly-Palm"
    payee: str = "SPS Mortgage Servicing"
    flag: str = "*"
    currency: str = "USD"
    tags: tuple[str, ...] = (
        "2943-butterfly-palm",
        "beangulp",
        "imported",
        "mortgage",
    )
