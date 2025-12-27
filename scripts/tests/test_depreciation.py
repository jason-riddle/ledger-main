#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pytest>=7.0.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Unit tests for depreciation utility functions.

Tests verify IRS depreciation calculations including:
- Annual depreciation amounts
- Monthly depreciation amounts
- First year depreciation with mid-month convention
- Last year depreciation with mid-month convention
- Remaining basis calculations
"""

import decimal
import pathlib
import sys

import pytest
import yaml  # type: ignore[import-untyped]

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from utils import depreciation


@pytest.fixture
def fixtures():
    """Load test fixtures from YAML file."""
    fixtures_dir = pathlib.Path(__file__).parent / "fixtures"
    fixture_path = fixtures_dir / "depreciation_fixtures.yaml"
    with open(fixture_path, encoding="utf-8") as fixture_file:
        return yaml.safe_load(fixture_file)


def test_calculate_annual_depreciation(fixtures):
    """Test annual depreciation calculations match expected values."""
    for asset in fixtures["assets"]:
        result = depreciation.calculate_annual_depreciation(
            asset["cost_basis"], asset["recovery_years"]
        )
        expected = decimal.Decimal(str(asset["expected_annual"]))
        assert result == expected, f"{asset['name']}: Expected {expected}, got {result}"


def test_calculate_monthly_depreciation(fixtures):
    """Test monthly depreciation calculations match expected values."""
    for asset in fixtures["assets"]:
        result = depreciation.calculate_monthly_depreciation(
            asset["cost_basis"], asset["recovery_years"]
        )
        expected = decimal.Decimal(str(asset["expected_monthly"]))
        assert result == expected, f"{asset['name']}: Expected {expected}, got {result}"


def test_calculate_first_year_depreciation(fixtures):
    """Test first year depreciation with mid-month convention."""
    for asset in fixtures["assets"]:
        result = depreciation.calculate_first_year_depreciation(
            asset["cost_basis"], asset["recovery_years"], asset["month_placed"]
        )
        expected = decimal.Decimal(str(asset["expected_first_year"]))
        assert result == expected, f"{asset['name']}: Expected {expected}, got {result}"


def test_calculate_last_year_depreciation(fixtures):
    """Test last year depreciation with mid-month convention."""
    for asset in fixtures["assets"]:
        result = depreciation.calculate_last_year_depreciation(
            asset["cost_basis"], asset["recovery_years"], asset["month_placed"]
        )
        expected = decimal.Decimal(str(asset["expected_last_year"]))
        assert result == expected, f"{asset['name']}: Expected {expected}, got {result}"


def test_calculate_remaining_basis():
    """Test remaining basis calculation."""
    # Example: 2943 Butterfly Palm Building after 2 years (2023-2024)
    # Cost: $164,791, Accumulated: $11,735.40
    result = depreciation.calculate_remaining_basis(164791, 11735.40)
    expected = decimal.Decimal("153055.60")
    assert result == expected


def test_first_year_depreciation_month_validation():
    """Test that invalid months raise ValueError."""
    pattern = "month_placed must be between 1 and 12"
    with pytest.raises(ValueError, match=pattern):
        depreciation.calculate_first_year_depreciation(10000, 27.5, 0)

    with pytest.raises(ValueError, match=pattern):
        depreciation.calculate_first_year_depreciation(10000, 27.5, 13)


def test_last_year_depreciation_month_validation():
    """Test that invalid months raise ValueError."""
    pattern = "month_placed must be between 1 and 12"
    with pytest.raises(ValueError, match=pattern):
        depreciation.calculate_last_year_depreciation(10000, 27.5, 0)

    with pytest.raises(ValueError, match=pattern):
        depreciation.calculate_last_year_depreciation(10000, 27.5, 13)


def test_mid_month_convention_january():
    """
    Test mid-month convention for January placement.

    For an asset placed in service in January (month 1):
    - First year months: 12 - 1 + 0.5 = 11.5 months
    - Last year months: 1 - 0.5 = 0.5 months
    """
    cost_basis = 10000
    recovery_years = 27.5

    monthly = depreciation.calculate_monthly_depreciation(cost_basis, recovery_years)

    first_year = depreciation.calculate_first_year_depreciation(
        cost_basis, recovery_years, 1
    )
    last_year = depreciation.calculate_last_year_depreciation(
        cost_basis, recovery_years, 1
    )

    # First year should be 11.5 months worth
    expected_first = monthly * decimal.Decimal("11.5")
    assert first_year == expected_first.quantize(decimal.Decimal("0.01"))

    # Last year should be 0.5 months worth
    expected_last = monthly * decimal.Decimal("0.5")
    assert last_year == expected_last.quantize(decimal.Decimal("0.01"))


def test_mid_month_convention_december():
    """
    Test mid-month convention for December placement.

    For an asset placed in service in December (month 12):
    - First year months: 12 - 12 + 0.5 = 0.5 months
    - Last year months: 12 - 0.5 = 11.5 months
    """
    cost_basis = 10000
    recovery_years = 27.5

    monthly = depreciation.calculate_monthly_depreciation(cost_basis, recovery_years)

    first_year = depreciation.calculate_first_year_depreciation(
        cost_basis, recovery_years, 12
    )
    last_year = depreciation.calculate_last_year_depreciation(
        cost_basis, recovery_years, 12
    )

    # First year should be 0.5 months worth
    expected_first = monthly * decimal.Decimal("0.5")
    assert first_year == expected_first.quantize(decimal.Decimal("0.01"))

    # Last year should be 11.5 months worth
    expected_last = monthly * decimal.Decimal("11.5")
    assert last_year == expected_last.quantize(decimal.Decimal("0.01"))


def test_total_depreciation_by_months():
    """
    Test that total depreciation calculated monthly equals cost basis.

    For any recovery period, total months * monthly rate should approximately
    equal the cost basis (within rounding tolerance).
    """
    # Allow $2 tolerance due to rounding across 330 months
    MAX_ROUNDING_TOLERANCE = decimal.Decimal("2.00")

    cost_basis = 164791
    recovery_years = 27.5

    monthly = depreciation.calculate_monthly_depreciation(cost_basis, recovery_years)
    total_months = decimal.Decimal(str(recovery_years)) * decimal.Decimal("12")

    total = monthly * total_months

    # Should be very close to cost basis (within $2 due to rounding)
    difference = abs(total - decimal.Decimal(str(cost_basis)))
    assert difference < MAX_ROUNDING_TOLERANCE, (
        f"Total depreciation {total} differs from cost basis {cost_basis} "
        f"by {difference}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
