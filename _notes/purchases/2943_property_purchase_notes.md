# Property Purchase Notes: 2943 Butterfly Palm

**Source Document:** `2022-10-21 2943 Butterfly Palm Closing - HUD-1 Settlement Statement.pdf`
**Date:** October 21, 2022
**File Number:** 092236345
**Loan Number:** 10003510

## Transaction Entities
*   **Borrower:** Jason Riddle
*   **Seller:** David D. New
*   **Lender:** MoFin Lending Corporation
*   **Settlement Agent:** Priority Settlement Group of Texas, LLC

---

## 1. Financial Summary (Page 1)

### J. Summary of Borrower's Transaction
| Line | Description | Amount (USD) | Notes |
| :--- | :--- | :--- | :--- |
| **100** | **Gross Amount Due from Borrower** | | |
| 101 | Contract Sales Price | 205,000.00 | Basis |
| 103 | Settlement Charges to Borrower | 5,613.08 | See Section L details |
| 104 | HOA Dues Paid Annually | 25.68 | Proration (10/22/22 - 12/31/22) |
| 107 | County Taxes (Reimbursement) | 682.71 | Proration (10/22/22 - 12/31/22) |
| **120** | **GROSS AMOUNT DUE** | **211,321.47** | |
| | | | |
| **200** | **Amounts Paid by or on Behalf of Borrower** | | |
| 201 | Deposit / Earnest Money | 2,250.00 | Credited against purchase |
| 202 | Principal Amount of New Loan | 102,500.00 | Mortgage Liability |
| **220** | **TOTAL PAID BY/FOR BORROWER** | **104,750.00** | |
| | | | |
| **300** | **Cash at Settlement** | | |
| 301 | Gross Amount Due (Line 120) | 211,321.47 | |
| 302 | Less Amounts Paid (Line 220) | (104,750.00) | |
| **303** | **CASH FROM BORROWER** | **106,571.47** | **The final wire amount** |

---

## 2. Settlement Charges Detail (Section L)

### 800. Items Payable in Connection with Loan
*These items are typically amortized loan costs or capitalized.*

| Line | Description | Amount | Beancount Treatment |
| :--- | :--- | :--- | :--- |
| 801 | Our origination charge | 1,793.75 | `Assets:Loan-Costs` |
| 804 | Appraisal fee (POC) | 750.00 | *Paid Outside Closing* (Not in totals) |
| 805 | Application Fee (POC) | 299.00 | *Paid Outside Closing* (Not in totals) |
| 806 | Document Review Fee | 595.00 | `Assets:Loan-Costs` |

### 900. Items Required by Lender to be Paid in Advance
*Prepaid expenses (deductible in year of purchase typically).*

| Line | Description | Amount | Beancount Treatment |
| :--- | :--- | :--- | :--- |
| 901 | Daily Interest Charges | 270.13 | `Expenses:Mortgage-Interest` (10/21-11/01) |
| 903 | Homeowner's Insurance | 1,067.00 | `Expenses:Insurance` (1 Year Premium) |

### 1000. Reserves Deposited with Lender
*Escrow account funding - this is an Asset transfer, not an expense.*

| Line | Description | Amount | Beancount Treatment |
| :--- | :--- | :--- | :--- |
| 1001 | **Initial Deposit for Escrow** | **762.80** | `Assets:Escrow:Taxes---Insurance` |
| *Breakdown* | *Homeowner's Ins (3 mo)* | *266.76* | |
| *Breakdown* | *Property Taxes (2 mo)* | *584.96* | |
| *Breakdown* | *Aggregate Adjustment* | *(88.92)* | |

### 1100. Title Charges
*Generally added to the Cost Basis of the property.*

| Line | Description | Amount | Beancount Treatment |
| :--- | :--- | :--- | :--- |
| 1101 | Title services & Lender's Title Ins | 100.00 | `Assets:Capital-Improvements...` (Basis) |
| 1109 | Settlement Fee | 399.00 | `Assets:Capital-Improvements...` (Basis) |
| 1111 | TLTA Endorsement T-19 | 50.00 | `Assets:Capital-Improvements...` (Basis) |
| 1112 | Endorsement T-30 | 20.00 | `Assets:Capital-Improvements...` (Basis) |
| 1113 | Endorsement T-36 | 25.00 | `Assets:Capital-Improvements...` (Basis) |
| 1114 | Endorsement T-17 | 25.00 | `Assets:Capital-Improvements...` (Basis) |
| *Note* | *Owner's Title Ins ($1,385) was paid by Seller* | | |

### 1200. Government Recording and Transfer Charges
*Added to Cost Basis.*

| Line | Description | Amount | Beancount Treatment |
| :--- | :--- | :--- | :--- |
| 1201 | Government recording charges | 168.40 | `Assets:Capital-Improvements...` (Basis) |
| *1206* | *(Includes E-Record Fee)* | *(14.40)* | |

### 1300. Additional Settlement Charges

| Line | Description | Amount | Beancount Treatment |
| :--- | :--- | :--- | :--- |
| 1303 | HOA New Account set up | 335.00 | `Assets:Capital-Improvements...` (Basis) |
| 1305 | GTY FEE - LTP | 2.00 | `Assets:Capital-Improvements...` (Basis) |

### 1400. Total Settlement Charges
**Total Borrower Charges:** **$5,613.08**

---

## 3. Cost Basis Calculation
*Reconstruction of the capitalized asset value for the ledger.*

1.  **Contract Price:** $205,000.00
2.  **Capitalized Closing Costs:**
    *   Title/Lender Ins (1101): $100.00
    *   Settlement Fee (1109): $399.00
    *   Endorsements (1111-1114): $120.00
    *   Recording Fees (1201): $168.40
    *   HOA Setup (1303): $335.00
    *   GTY Fee (1305): $2.00
    *   **Subtotal Costs:** $1,124.40
3.  **Total Cost Basis:** **$206,124.40**

## 4. Loan Cost Capitalization
*Amortizable costs separate from property basis.*

1.  Origination Charge (801): $1,793.75
2.  Document Review Fee (806): $595.00
3.  **Total Loan Costs:** **$2,388.75**

## 5. Ledger Reconciliation Check
Summing the debits (outflows/costs) to equal the credits (funding).

**Debits (Uses of Funds):**
*   Basis (Land+Building): $206,124.40
*   Loan Costs: $2,388.75
*   Prepaid Interest: $270.13
*   Prepaid Insurance: $1,067.00
*   Escrow Deposit: $762.80
*   Tax Reimbursement: $682.71
*   HOA Proration: $25.68
*   **Total Uses:** **$211,321.47**

**Credits (Sources of Funds):**
*   Mortgage Loan: $102,500.00
*   Earnest Money: $2,250.00
*   Cash to Close: $106,571.47
*   **Total Sources:** **$211,321.47**

**Result:** The transaction balances exactly.
