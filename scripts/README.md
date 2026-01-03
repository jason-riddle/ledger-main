# Ledger Verification Scripts

Python scripts to verify the accuracy of depreciation and loan amortization calculations in the Beancount ledger.

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

Install uv:
```bash
pip install uv
```

## Scripts

### Verification Scripts

#### `verify_depreciation.py`
Verifies that depreciation transactions match IRS rules:
- 27.5-year straight-line for residential rental buildings and improvements
- 30-year straight-line for loan costs
- Mid-month convention for first/last year

**Usage:**
```bash
# Run with uv (recommended)
uv run scripts/depreciation/verify_depreciation.py

# Or run directly
./scripts/depreciation/verify_depreciation.py
```

**Example output:**
```
📋 2943 Butterfly Palm Building
   Cost Basis: $164,791.00
   Recovery: 27.5 years
   Expected Monthly: $499.37
   Transactions: 37
   ✓ All 37 transactions correct
```

#### `verify_amortization.py`
Verifies mortgage payment calculations using standard amortization formulas:
- Monthly interest = (Annual Rate / 12) × Remaining Balance
- Principal payment = Total Payment - Interest

**Usage:**
```bash
# Run with uv (recommended)
uv run scripts/amortization/verify_amortization.py

# Or run directly
./scripts/amortization/verify_amortization.py
```

**Example output:**
```
📋 2943 Butterfly Palm Mortgage
   Original Principal: $102,500.00
   Annual Rate: 8.625%
   Expected P+I Payment: $797.23
   Payments Found: 37
   ✓ All 37 payments verified correctly
```

**Exit codes:**
- `0` - All calculations verified successfully
- `1` - Discrepancies found or errors occurred

#### `calculate_amortization.py`
Calculates amortization details and emits JSON:
- Summary (monthly payment, total interest, total paid)
- Optional point lookup (by month number or date)
- Optional range output (by month numbers or dates)

**Usage:**
```bash
# Summary only
uv run scripts/amortization/calculate_amortization.py \
  --principal 102500 --annual-rate 8.625 --term-years 30

# Point lookup by month
uv run scripts/amortization/calculate_amortization.py \
  --principal 102500 --annual-rate 8.625 --term-years 30 \
  --month 12

# Point lookup by date (requires start-date)
uv run scripts/amortization/calculate_amortization.py \
  --principal 102500 --annual-rate 8.625 --term-years 30 \
  --start-date 2023-01 --date 2024-06

# Range by month
uv run scripts/amortization/calculate_amortization.py \
  --principal 102500 --annual-rate 8.625 --term-years 30 \
  --from-month 1 --to-month 12

# Full schedule
uv run scripts/amortization/calculate_amortization.py \
  --principal 102500 --annual-rate 8.625 --term-years 30 \
  --full-schedule
```

#### `calculate_depreciation.py`
Generates Beancount depreciation postings (straight-line, mid-month convention):
- Yearly output (`--year`) or date-range output (`--from-date`/`--to-date`)
- First-year annual or monthly output (`--first-year-mode`)
- Optional end-date truncation (`--end-date`)
- Optional balance assertion (`--include-balance`)

**Usage:**
```bash
# Yearly postings (monthly)
uv run scripts/depreciation/calculate_depreciation.py \
  --asset-name "2943 Butterfly Palm Building" \
  --placed-in-service 2023-01-01 \
  --cost-basis 164791 \
  --recovery-years 27.5 \
  --accum-account "Assets:Accumulated-Depreciation:2943-Butterfly-Palm:Building:2023-01-01-Building" \
  --expense-account "Expenses:Depreciation:2943-Butterfly-Palm" \
  --year 2024 \
  --first-year-mode monthly

# First-year annual posting (rounded to whole dollars)
uv run scripts/depreciation/calculate_depreciation.py \
  --asset-name "206 Hoover Ave Building" \
  --placed-in-service 2023-05-26 \
  --cost-basis 73358 \
  --recovery-years 27.5 \
  --accum-account "Assets:Accumulated-Depreciation:206-Hoover-Ave:Building:2023-05-26-Building" \
  --expense-account "Expenses:Depreciation:206-Hoover-Ave" \
  --year 2023 \
  --first-year-mode annual \
  --include-balance \
  --starting-accumulated 0

# Date range with an end-date cut-off
uv run scripts/depreciation/calculate_depreciation.py \
  --asset-name "2943 Butterfly Palm Water Heater" \
  --placed-in-service 2024-05-08 \
  --cost-basis 2800.75 \
  --recovery-years 27.5 \
  --accum-account "Assets:Accumulated-Depreciation:2943-Butterfly-Palm:Improvements:2024-05-08-Water-Heater" \
  --expense-account "Expenses:Depreciation:2943-Butterfly-Palm" \
  --from-date 2024-05 \
  --to-date 2024-12 \
  --end-date 2024-10-31 \
  --first-year-mode monthly
```

### Utility Modules

#### `depreciation/utils/depreciation.py`
IRS depreciation calculation functions:
- `calculate_annual_depreciation(cost_basis, recovery_years)`
- `calculate_monthly_depreciation(cost_basis, recovery_years)`
- `calculate_first_year_depreciation(cost_basis, recovery_years, month_placed)`
- `calculate_last_year_depreciation(cost_basis, recovery_years, month_placed)`
- `calculate_remaining_basis(cost_basis, accumulated_depreciation)`

#### `amortization/utils/amortization.py`
Loan amortization calculation functions:
- `calculate_monthly_payment(principal, annual_rate, term_years)`
- `calculate_interest_payment(balance, annual_rate)`
- `calculate_principal_payment(total_payment, interest_payment)`
- `generate_amortization_schedule(principal, annual_rate, term_years, start_month=1)`

### Unit Tests

Run unit tests to verify the utility functions:

```bash
# Test depreciation utilities
uv run scripts/depreciation/tests/test_depreciation.py

# Test amortization utilities
uv run scripts/amortization/tests/test_amortization.py

# Or run all tests
uv run pytest scripts/amortization/tests/ scripts/depreciation/tests/
```

## Implementation Details

### IRS Depreciation Rules

**Straight-Line Method:**
- Annual depreciation = Cost Basis ÷ Recovery Years
- Monthly depreciation = Annual ÷ 12

**Mid-Month Convention:**
- Asset is assumed placed in service in the middle of the month
- First year: months in service = 12 - month_placed + 0.5
- Last year: months in service = month_placed - 0.5

**Recovery Periods:**
- Residential rental buildings and improvements: 27.5 years
- Loan costs: 30 years

### Standard Amortization Formula

**Monthly Payment:**
```
M = P × [r(1+r)^n] / [(1+r)^n - 1]
```
Where:
- M = monthly payment
- P = principal loan amount
- r = monthly interest rate (annual rate / 12)
- n = total number of payments

**Interest and Principal Split:**
- Monthly interest = (Annual Rate / 12) × Remaining Balance
- Principal payment = Monthly Payment - Interest
- New balance = Old Balance - Principal

## Test Fixtures

Test fixtures are stored in `scripts/amortization/tests/fixtures/` and\n+`scripts/depreciation/tests/fixtures/`:
- `depreciation_fixtures.yaml` - Expected values for known assets
- `amortization_fixtures.yaml` - Expected values for mortgage payments

These fixtures are used by unit tests to validate calculations against known correct values.

## Dependencies

All scripts use inline script metadata (PEP 723) for dependency management:
- `beancount>=3.0.0` - For ledger parsing
- `pytest>=7.0.0` - For unit tests
- `pyyaml>=6.0` - For fixture loading

Dependencies are automatically installed when running with `uv run`.
