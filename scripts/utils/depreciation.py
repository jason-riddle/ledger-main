"""
IRS Depreciation Calculation Utilities.

This module provides functions to calculate depreciation for rental property
assets following IRS rules:
- 27.5-year straight-line for residential rental buildings and improvements
- 30-year straight-line for loan costs
- Mid-month convention (assets placed in service mid-month)

Key IRS Rules:
- Modified Accelerated Cost Recovery System (MACRS)
- Straight-line method for residential rental property
- Mid-month convention: asset is assumed placed in service in middle of month
- First year: depreciation = (annual / 12) * (12 - month_placed + 0.5)
- Full years: annual depreciation amount
- Last year: remaining basis or partial year amount
"""

import decimal

# Month validation constants
MIN_MONTH = 1
MAX_MONTH = 12


def calculate_annual_depreciation(
    cost_basis: float, recovery_years: float
) -> decimal.Decimal:
    """
    Calculate annual depreciation amount using straight-line method.

    Args:
        cost_basis: The depreciable basis of the asset in dollars
        recovery_years: The IRS recovery period (27.5 for buildings, 30 for
            loan costs)

    Returns:
        Annual depreciation amount rounded to 2 decimal places

    Example:
        >>> calculate_annual_depreciation(164791, 27.5)
        Decimal('5992.40')
    """
    annual = decimal.Decimal(str(cost_basis)) / decimal.Decimal(str(recovery_years))
    return annual.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)


def calculate_monthly_depreciation(
    cost_basis: float, recovery_years: float
) -> decimal.Decimal:
    """
    Calculate monthly depreciation amount using straight-line method.

    Args:
        cost_basis: The depreciable basis of the asset in dollars
        recovery_years: The IRS recovery period (27.5 for buildings, 30 for
            loan costs)

    Returns:
        Monthly depreciation amount rounded to 2 decimal places

    Example:
        >>> calculate_monthly_depreciation(164791, 27.5)
        Decimal('499.37')
    """
    annual = calculate_annual_depreciation(cost_basis, recovery_years)
    monthly = annual / decimal.Decimal("12")
    return monthly.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)


def calculate_first_year_depreciation(
    cost_basis: float, recovery_years: float, month_placed: int
) -> decimal.Decimal:
    """
    Calculate first year depreciation using mid-month convention.

    IRS mid-month convention: Asset is treated as placed in service in the
    middle of the month. For month placed in service, count 0.5 months.

    Formula: (annual / 12) * (12 - month_placed + 0.5)

    Args:
        cost_basis: The depreciable basis of the asset in dollars
        recovery_years: The IRS recovery period (27.5 for buildings, 30 for
            loan costs)
        month_placed: Month asset was placed in service (1-12, where 1=January)

    Returns:
        First year depreciation amount rounded to 2 decimal places

    Example:
        >>> calculate_first_year_depreciation(164791, 27.5, 1)
        Decimal('5742.93')  # (5992.40 / 12) * (12 - 1 + 0.5) = 5742.93
    """
    if not MIN_MONTH <= month_placed <= MAX_MONTH:
        raise ValueError(
            "month_placed must be between "
            f"{MIN_MONTH} and {MAX_MONTH}, got {month_placed}"
        )

    monthly = calculate_monthly_depreciation(cost_basis, recovery_years)
    months_in_service = (
        decimal.Decimal("12")
        - decimal.Decimal(str(month_placed))
        + decimal.Decimal("0.5")
    )
    first_year = monthly * months_in_service
    return first_year.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)


def calculate_remaining_basis(
    cost_basis: float, accumulated_depreciation: float
) -> decimal.Decimal:
    """
    Calculate remaining depreciable basis of an asset.

    Args:
        cost_basis: The original depreciable basis of the asset in dollars
        accumulated_depreciation: Total depreciation taken to date in dollars

    Returns:
        Remaining basis rounded to 2 decimal places

    Example:
        >>> calculate_remaining_basis(164791, 11735.40)
        Decimal('153055.60')
    """
    remaining = decimal.Decimal(str(cost_basis)) - decimal.Decimal(
        str(accumulated_depreciation)
    )
    return remaining.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)


def calculate_last_year_depreciation(
    cost_basis: float, recovery_years: float, month_placed: int
) -> decimal.Decimal:
    """
    Calculate last year (final year) depreciation using mid-month convention.

    In the final year, only partial depreciation is taken for the remaining
    months.
    Formula: (annual / 12) * (month_placed - 0.5)

    Args:
        cost_basis: The depreciable basis of the asset in dollars
        recovery_years: The IRS recovery period (27.5 for buildings, 30 for
            loan costs)
        month_placed: Month asset was placed in service (1-12, where 1=January)

    Returns:
        Last year depreciation amount rounded to 2 decimal places

    Example:
        >>> calculate_last_year_depreciation(164791, 27.5, 1)
        Decimal('249.69')  # (5992.40 / 12) * (1 - 0.5) = 249.69
    """
    if not MIN_MONTH <= month_placed <= MAX_MONTH:
        raise ValueError(
            "month_placed must be between "
            f"{MIN_MONTH} and {MAX_MONTH}, got {month_placed}"
        )

    monthly = calculate_monthly_depreciation(cost_basis, recovery_years)
    months_in_final_year = decimal.Decimal(str(month_placed)) - decimal.Decimal("0.5")
    last_year = monthly * months_in_final_year
    return last_year.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
