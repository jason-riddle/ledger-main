#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pytest>=7.0.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Unit tests for amortization utility functions.

Tests verify standard loan amortization calculations including:
- Monthly payment calculation
- Interest payment calculation
- Principal payment calculation
- Full amortization schedule generation
"""

import pytest
import yaml
from decimal import Decimal
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.amortization import (
    calculate_monthly_payment,
    calculate_interest_payment,
    calculate_principal_payment,
    generate_amortization_schedule,
)


@pytest.fixture
def fixtures():
    """Load test fixtures from YAML file."""
    fixture_path = Path(__file__).parent / "fixtures" / "amortization_fixtures.yaml"
    with open(fixture_path) as f:
        return yaml.safe_load(f)


def test_calculate_monthly_payment(fixtures):
    """Test monthly payment calculation matches expected value."""
    loan = fixtures['loan']
    result = calculate_monthly_payment(
        loan['original_principal'],
        loan['annual_rate'],
        loan['term_years']
    )
    expected = Decimal(str(loan['expected_monthly_payment']))
    assert result == expected, f"Expected {expected}, got {result}"


def test_calculate_interest_payment(fixtures):
    """Test interest payment calculations for multiple months."""
    loan = fixtures['loan']
    
    for payment in fixtures['payments']:
        result = calculate_interest_payment(
            payment['balance_before'],
            loan['annual_rate']
        )
        expected = Decimal(str(payment['expected_interest']))
        assert result == expected, (
            f"Month {payment['month']}: Expected {expected}, got {result}"
        )


def test_calculate_principal_payment(fixtures):
    """Test principal payment calculations."""
    loan = fixtures['loan']
    monthly_payment = loan['expected_monthly_payment']
    
    for payment in fixtures['payments']:
        result = calculate_principal_payment(
            monthly_payment,
            payment['expected_interest']
        )
        expected = Decimal(str(payment['expected_principal']))
        assert result == expected, (
            f"Month {payment['month']}: Expected {expected}, got {result}"
        )


def test_generate_amortization_schedule(fixtures):
    """Test full amortization schedule generation."""
    loan = fixtures['loan']
    
    schedule = generate_amortization_schedule(
        loan['original_principal'],
        loan['annual_rate'],
        loan['term_years']
    )
    
    # Should have 360 payments (30 years * 12 months)
    assert len(schedule) == 360
    
    # Verify first 12 months match fixtures
    for i, payment in enumerate(fixtures['payments']):
        month_data = schedule[i]
        
        assert month_data['month'] == payment['month']
        
        # Check balance before
        expected_balance = Decimal(str(payment['balance_before']))
        assert month_data['balance_before'] == expected_balance, (
            f"Month {payment['month']} balance_before: "
            f"Expected {expected_balance}, got {month_data['balance_before']}"
        )
        
        # Check interest (allow small rounding difference)
        expected_interest = Decimal(str(payment['expected_interest']))
        interest_diff = abs(month_data['interest'] - expected_interest)
        assert interest_diff <= Decimal('0.01'), (
            f"Month {payment['month']} interest: "
            f"Expected {expected_interest}, got {month_data['interest']}"
        )
        
        # Check principal (allow small rounding difference)
        expected_principal = Decimal(str(payment['expected_principal']))
        principal_diff = abs(month_data['principal'] - expected_principal)
        assert principal_diff <= Decimal('0.01'), (
            f"Month {payment['month']} principal: "
            f"Expected {expected_principal}, got {month_data['principal']}"
        )


def test_amortization_schedule_final_balance_zero(fixtures):
    """Test that final payment brings balance to exactly zero."""
    loan = fixtures['loan']
    
    schedule = generate_amortization_schedule(
        loan['original_principal'],
        loan['annual_rate'],
        loan['term_years']
    )
    
    # Final balance should be exactly zero
    final_payment = schedule[-1]
    assert final_payment['balance_after'] == Decimal('0'), (
        f"Final balance should be 0, got {final_payment['balance_after']}"
    )


def test_amortization_schedule_decreasing_balance(fixtures):
    """Test that loan balance decreases with each payment."""
    loan = fixtures['loan']
    
    schedule = generate_amortization_schedule(
        loan['original_principal'],
        loan['annual_rate'],
        loan['term_years']
    )
    
    for i in range(len(schedule) - 1):
        current_balance = schedule[i]['balance_after']
        next_balance = schedule[i + 1]['balance_before']
        
        # Balance should decrease
        assert current_balance >= next_balance, (
            f"Balance should decrease: month {i+1} after={current_balance}, "
            f"month {i+2} before={next_balance}"
        )
        
        # Balance after payment i should equal balance before payment i+1
        assert current_balance == next_balance, (
            f"Balance continuity error: month {i+1} after={current_balance}, "
            f"month {i+2} before={next_balance}"
        )


def test_amortization_schedule_interest_decreases(fixtures):
    """Test that interest portion decreases over time."""
    loan = fixtures['loan']
    
    schedule = generate_amortization_schedule(
        loan['original_principal'],
        loan['annual_rate'],
        loan['term_years']
    )
    
    # Interest should generally decrease (with small rounding exceptions)
    first_year_avg_interest = sum(p['interest'] for p in schedule[:12]) / 12
    last_year_avg_interest = sum(p['interest'] for p in schedule[-12:]) / 12
    
    assert first_year_avg_interest > last_year_avg_interest, (
        f"Interest should decrease over time: "
        f"First year avg={first_year_avg_interest}, "
        f"Last year avg={last_year_avg_interest}"
    )


def test_amortization_schedule_principal_increases(fixtures):
    """Test that principal portion increases over time."""
    loan = fixtures['loan']
    
    schedule = generate_amortization_schedule(
        loan['original_principal'],
        loan['annual_rate'],
        loan['term_years']
    )
    
    # Principal should generally increase (with small rounding exceptions)
    first_year_avg_principal = sum(p['principal'] for p in schedule[:12]) / 12
    last_year_avg_principal = sum(p['principal'] for p in schedule[-12:]) / 12
    
    assert first_year_avg_principal < last_year_avg_principal, (
        f"Principal should increase over time: "
        f"First year avg={first_year_avg_principal}, "
        f"Last year avg={last_year_avg_principal}"
    )


def test_amortization_schedule_with_start_month(fixtures):
    """Test that start_month parameter works correctly."""
    loan = fixtures['loan']
    
    # Generate schedule starting from month 15 (to match 2024 payments)
    schedule = generate_amortization_schedule(
        loan['original_principal'],
        loan['annual_rate'],
        loan['term_years'],
        start_month=15
    )
    
    # First entry should be month 15
    assert schedule[0]['month'] == 15
    
    # Last entry should be month 374 (15 + 360 - 1)
    assert schedule[-1]['month'] == 374


def test_interest_calculation_spot_checks():
    """Test interest calculation with known values."""
    # 8.625% annual = 0.71875% monthly
    # Balance $100,000 should yield $718.75 interest
    result = calculate_interest_payment(100000, 8.625)
    expected = Decimal('718.75')
    assert result == expected
    
    # Balance $50,000 should yield $359.38 interest (rounded)
    result = calculate_interest_payment(50000, 8.625)
    expected = Decimal('359.38')
    assert result == expected


def test_monthly_payment_formula_validation():
    """
    Test monthly payment formula with known mortgage values.
    
    Validates the standard amortization formula:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    """
    # Test case from fixtures: $102,500 at 8.625% for 30 years
    result = calculate_monthly_payment(102500, 8.625, 30)
    expected = Decimal('797.23')
    assert result == expected
    
    # Additional test: $200,000 at 5% for 30 years should be ~$1,073.64
    result = calculate_monthly_payment(200000, 5.0, 30)
    expected = Decimal('1073.64')
    assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
