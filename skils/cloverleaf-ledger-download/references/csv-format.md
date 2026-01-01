# CSV Format Specification

The output CSV uses semicolon (;) as field separator and double quotes for all fields.

## Headers
"Account";"Property / Unit";"Date Posted";"Payee / Payer";"Description";"Reference";"Increase";"Decrease";"Balance"

## Data Format
- **Account**: Transaction account type (e.g., "Rent", "Management Fee Expense")
- **Property / Unit**: Property address on one line (e.g., "2943 Butterfly Palm San Antonio TX 78245")
- **Date Posted**: Date in MM-DD-YYYY format (e.g., "01-01-2026")
- **Payee / Payer**: Entity name (e.g., "Layla Rain Robertson", "CloverLeaf Property Management")
- **Description**: Transaction description
- **Reference**: Transaction reference ID or empty
- **Increase**: Positive amount with $ (e.g., "$1,600.00") or "$0.00"
- **Decrease**: Negative amount with $ or "$0.00"
- **Balance**: Running balance with $

## Filename Format
cloverleaf-{earliest_date}-to-{latest_date}-ledger.csv

Where dates are in YYYY-MM-DD format, determined from the Date Posted column.

## Examples

### Example: Multiple transactions with starting balance

**Input HTML:**
```html
<table class="table-data table table-striped table-hover">
<thead>
<tr>
<th>Account</th>
<th>Property / Unit</th>
<th>Date Posted</th>
<th>Payee / Payer</th>
<th>Description</th>
<th>Reference</th>
<th>Increase</th>
<th>Decrease</th>
<th>Balance</th>
</tr>
</thead>
<tbody>
<tr>
<td><span>Utilities</span></td>
<td><div>206 Hoover Ave <br>San Antonio TX 78225</div></td>
<td><time datetime="1766390400000">12-22-2025</time></td>
<td><span>CPS Energy</span></td>
<td><span>Electric/Gas Bill - 11/13/25 to 12/9/25</span></td>
<td><span></span></td>
<td><span>$0.00</span></td>
<td><div class="MuiBox-root css-0"><span>$63.98</span></div></td>
<td><div class="MuiBox-root css-0"><span>$761.02</span></div></td>
</tr>
<tr>
<td><span>Management Fee Expense</span></td>
<td><div>206 Hoover Ave <br>San Antonio TX 78225</div></td>
<td><time datetime="1765958400000">12-17-2025</time></td>
<td><span>CloverLeaf Property Management</span></td>
<td><span>Appliance - Accept delivery</span></td>
<td><span></span></td>
<td><span>$0.00</span></td>
<td><div class="MuiBox-root css-0"><span>$75.00</span></div></td>
<td><div class="MuiBox-root css-0"><span>$825.00</span></div></td>
</tr>
<tr><td colspan="8">Starting Balance</td><td><div class="MuiBox-root css-0"><span>$900.00</span></div></td></tr>
</tbody>
</table>
```

**Expected CSV Output:**
```
"Account";"Property / Unit";"Date Posted";"Payee / Payer";"Description";"Reference";"Increase";"Decrease";"Balance"
"Utilities";"206 Hoover Ave San Antonio TX 78225";"12-22-2025";"CPS Energy";"Electric/Gas Bill - 11/13/25 to 12/9/25";"";"$0.00";"$63.98";"$761.02"
"Management Fee Expense";"206 Hoover Ave San Antonio TX 78225";"12-17-2025";"CloverLeaf Property Management";"Appliance - Accept delivery";"";"$0.00";"$75.00";"$825.00"
```

**Expected Filename:** `cloverleaf-2025-12-17-to-2025-12-22-ledger.csv`

## Notes
- Starting Balance rows are excluded from CSV output
- All fields are quoted and quotes within fields are escaped by doubling
- Addresses have &lt;br&gt; tags converted to spaces
