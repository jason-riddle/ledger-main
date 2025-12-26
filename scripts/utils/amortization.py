"""
Loan Amortization Calculation Utilities.

This module provides functions to calculate loan amortization schedules
using standard mortgage formulas.

Standard Amortization Formulas:
- Monthly Payment = P * [r(1+r)^n] / [(1+r)^n - 1]
  where P = principal, r = monthly rate, n = number of payments
- Monthly Interest = (Annual Rate / 12) * Remaining Balance
- Principal Payment = Monthly Payment - Interest Payment
- New Balance = Old Balance - Principal Payment
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, TypedDict


class AmortizationEntry(TypedDict):
    month: int
    balance_before: Decimal
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance_after: Decimal


def calculate_monthly_payment(
    principal: float,
    annual_rate: float,
    term_years: int
) -> Decimal:
    """
    Calculate fixed monthly payment for a loan using standard amortization formula.

    Formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where:
        M = monthly payment
        P = principal loan amount
        r = monthly interest rate (annual rate / 12)
        n = total number of payments (term_years * 12)

    Args:
        principal: The loan principal amount in dollars
        annual_rate: Annual interest rate as a percentage (e.g., 8.625 for 8.625%)
        term_years: Loan term in years

    Returns:
        Monthly payment amount (principal + interest) rounded to 2 decimal places

    Example:
        >>> calculate_monthly_payment(102500, 8.625, 30)
        Decimal('797.23')
    """
    P = Decimal(str(principal))
    r = Decimal(str(annual_rate)) / Decimal('100') / Decimal('12')  # Monthly rate
    n = term_years * 12  # Total payments

    # M = P * [r(1+r)^n] / [(1+r)^n - 1]
    one_plus_r = Decimal('1') + r
    one_plus_r_to_n = one_plus_r ** n

    numerator = P * r * one_plus_r_to_n
    denominator = one_plus_r_to_n - Decimal('1')

    monthly_payment = numerator / denominator
    return monthly_payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_interest_payment(balance: float, annual_rate: float) -> Decimal:
    """
    Calculate interest payment for current month based on remaining balance.

    Formula: Interest = (Annual Rate / 12) * Balance

    Args:
        balance: Current loan balance in dollars
        annual_rate: Annual interest rate as a percentage (e.g., 8.625 for 8.625%)

    Returns:
        Monthly interest payment rounded to 2 decimal places

    Example:
        >>> calculate_interest_payment(102500, 8.625)
        Decimal('736.72')
    """
    balance_dec = Decimal(str(balance))
    monthly_rate = Decimal(str(annual_rate)) / Decimal('100') / Decimal('12')
    interest = balance_dec * monthly_rate
    return interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_principal_payment(total_payment: float, interest_payment: float) -> Decimal:
    """
    Calculate principal payment as the difference between total and interest.

    Formula: Principal = Total Payment - Interest Payment

    Args:
        total_payment: Total monthly payment (P+I) in dollars
        interest_payment: Interest portion of payment in dollars

    Returns:
        Principal payment amount rounded to 2 decimal places

    Example:
        >>> calculate_principal_payment(797.23, 736.72)
        Decimal('60.51')
    """
    principal = Decimal(str(total_payment)) - Decimal(str(interest_payment))
    return principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def generate_amortization_schedule(
    principal: float,
    annual_rate: float,
    term_years: int,
    start_month: int = 1
) -> List[AmortizationEntry]:
    """
    Generate a complete amortization schedule for a loan.

    Args:
        principal: The loan principal amount in dollars
        annual_rate: Annual interest rate as a percentage (e.g., 8.625 for 8.625%)
        term_years: Loan term in years
        start_month: Starting month number (default: 1)

    Returns:
        List of dictionaries containing payment details for each month:
        - month: Payment number
        - balance_before: Balance at start of month
        - payment: Total payment amount
        - interest: Interest portion
        - principal: Principal portion
        - balance_after: Balance at end of month

    Example:
        >>> schedule = generate_amortization_schedule(102500, 8.625, 30)
        >>> schedule[0]['month']
        1
        >>> schedule[0]['interest']
        Decimal('736.72')
    """
    monthly_payment = calculate_monthly_payment(principal, annual_rate, term_years)
    balance = Decimal(str(principal))
    schedule: List[AmortizationEntry] = []
    total_months = term_years * 12

    for month in range(start_month, start_month + total_months):
        balance_before = balance

        # Calculate interest and principal for this payment
        interest = calculate_interest_payment(float(balance), annual_rate)
        principal_pmt = calculate_principal_payment(float(monthly_payment), float(interest))

        # Update balance
        balance = balance - principal_pmt

        # Ensure final payment zeros out the balance
        if month == start_month + total_months - 1:
            # Adjust final payment to clear remaining balance
            principal_pmt = balance_before
            balance = Decimal('0')
            payment = interest + principal_pmt
        else:
            payment = monthly_payment

        schedule.append({
            'month': month,
            'balance_before': balance_before.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'payment': payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'interest': interest,
            'principal': principal_pmt,
            'balance_after': balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })

    return schedule
