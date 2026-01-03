# JSONL Transaction Schema

This directory contains the JSON Schema definition for the intermediate JSONL format used in the statement parsing pipeline.

## Overview

The flow for processing statements is:
```
.pdf → .pdf.txt → .pdf.jsonl → .pdf.bean
```

This schema defines the structure of the `.pdf.jsonl` file, which contains one JSON object per line (JSONL format), where each object represents a single financial transaction that can be converted to Beancount format.

## Schema File

- **`transaction.schema.json`** - JSON Schema (draft-07) defining the structure of transaction objects

## Transaction Object Structure

Each transaction object has the following top-level properties:

### Required Fields
- **`ok`** (boolean): Indicates if the transaction was successfully parsed
  - `true`: Transaction is valid and ready for conversion
  - `false`: Parsing failed, see `error` field

### Success Case (ok: true)
- **`transaction`** (object): Contains the normalized transaction data
  - **`date`** (string, ISO 8601): Transaction date (YYYY-MM-DD)
  - **`property`** (string enum): One of:
    - `"206-Hoover-Ave"`
    - `"2943-Butterfly-Palm"`
    - `"Unassigned"`
  - **`payee_payer`** (string): The payee or payer
  - **`description`** (string): Transaction description/narration
  - **`entries`** (array): Exactly 2 posting entries for double-entry accounting
    - Each entry has:
      - **`account`** (string): Full Beancount account name
      - **`amount_usd`** (number): Amount in USD (positive for debits, negative for credits)
    - Must sum to zero for valid double-entry
  - **`tags`** (array of strings, optional): Tags for categorization

### Failure Case (ok: false)
- **`error`** (string): Primary error message explaining why parsing failed

### Optional Fields (Both Cases)
- **`errors`** (array of strings): Additional warnings/issues
- **`notes`** (string): Additional context or information
- **`raw_input`** (string): Original input for debugging

## Examples

### Valid Transaction (Success)

```json
{
  "ok": true,
  "transaction": {
    "date": "2024-01-15",
    "property": "206-Hoover-Ave",
    "payee_payer": "Tenant",
    "description": "Monthly rent payment",
    "entries": [
      {
        "account": "Assets:Property-Management:CloverLeaf-PM",
        "amount_usd": 1500.00
      },
      {
        "account": "Income:Rent:206-Hoover-Ave",
        "amount_usd": -1500.00
      }
    ],
    "tags": ["rent", "206-hoover-ave", "operations"]
  }
}
```

### Failed Transaction

```json
{
  "ok": false,
  "error": "Unable to parse date from input",
  "raw_input": "Account, Property / Unit, Date Posted, ...",
  "errors": ["Date format not recognized: '01/32/2024'"],
  "notes": "Date appears to be invalid (day 32)"
}
```

### Transaction with Warnings

```json
{
  "ok": true,
  "transaction": {
    "date": "2024-06-20",
    "property": "2943-Butterfly-Palm",
    "payee_payer": "Contractor",
    "description": "Roof repair",
    "entries": [
      {
        "account": "Assets:Property-Management:CloverLeaf-PM",
        "amount_usd": -2800.00
      },
      {
        "account": "Expenses:Repairs:2943-Butterfly-Palm",
        "amount_usd": 2800.00
      }
    ],
    "tags": ["repairs", "2943-butterfly-palm", "operations"]
  },
  "errors": ["Amount $2800 near capital improvement threshold of $2500"],
  "notes": "Consider whether this should be capitalized"
}
```

## Validation

To validate a JSONL file against this schema, you can use JSON Schema validation tools such as:

- **Python**: `jsonschema` library
- **Node.js**: `ajv` package
- **Online**: https://www.jsonschemavalidator.net/

### Validation Script

Use the included validation script to check JSONL files:

```bash
# Validate a JSONL file
python schema/validate_jsonl.py path/to/file.jsonl

# Verbose output
python schema/validate_jsonl.py path/to/file.jsonl --verbose

# Use a different schema file
python schema/validate_jsonl.py path/to/file.jsonl --schema path/to/schema.json
```

Example Python validation:

```python
import json
import jsonschema

# Load schema
with open('schema/transaction.schema.json') as f:
    schema = json.load(f)

# Validate a transaction
transaction = {
    "ok": True,
    "transaction": {
        "date": "2024-01-15",
        "property": "206-Hoover-Ave",
        "payee_payer": "Tenant",
        "description": "Rent payment",
        "entries": [
            {"account": "Assets:Property-Management:CloverLeaf-PM", "amount_usd": 1500.00},
            {"account": "Income:Rent:206-Hoover-Ave", "amount_usd": -1500.00}
        ]
    }
}

jsonschema.validate(transaction, schema)
```

## Converting JSONL to Beancount

The included conversion script demonstrates the final step of the pipeline:

```bash
# Convert to stdout
python schema/jsonl_to_bean.py input.jsonl

# Convert to file
python schema/jsonl_to_bean.py input.jsonl output.bean
```

The script will:
- Skip failed transactions (ok=false)
- Convert successful transactions to Beancount format
- Report errors and warnings to stderr
- Output Beancount text to stdout or file

## Usage in Pipeline

1. **Input**: Parse `.pdf.txt` files from property management statements
2. **Process**: Convert each transaction line to a JSON object matching this schema
3. **Output**: Write JSON objects as JSONL (one per line) to `.pdf.jsonl`
4. **Next Step**: Convert `.pdf.jsonl` to `.pdf.bean` format

## Key Differences from Original YAML Schema

This simplified schema removes:
- **`reasoning`** fields on all properties (date, property, payee_payer, description, entries, tags)
- **`source`** field in transaction object
- Nested object wrappers that held `value` and `reasoning`

This makes the schema:
- More concise and easier to work with
- Faster to validate
- Simpler to generate programmatically
- Still contains all essential data needed to produce Beancount files

## Chart of Accounts

The schema validates against property values but does not enforce specific account names. Refer to the original YAML for the full chart of accounts used in this ledger system. Common account patterns include:

- `Assets:Property-Management:{Manager-PM}`
- `Assets:Cash---Bank:Checking`
- `Income:Rent:{Property}`
- `Expenses:Repairs:{Property}`
- `Expenses:Management-Fees:{Property}`
- `Equity:Owner-Distributions:Owner-Draw`
