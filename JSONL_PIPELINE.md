# JSONL Processing Pipeline

This document describes the JSONL processing pipeline for converting statement text files into Beancount format.

## Pipeline Overview

The processing pipeline consists of three stages:

```
.pdf → .pdf.txt → .pdf.jsonl → .pdf.bean
```

1. **PDF to Text**: Extract text from PDF statements (external tool, e.g., `pdftotext`)
2. **Text to JSONL**: Parse statement text and output structured JSON (this implementation)
3. **JSONL to Beancount**: Convert structured JSON to Beancount format (this implementation)

## Usage

### Generating JSONL from Statement Text

Use the `beanout` CLI with the `--jsonl` flag:

```bash
# SPS mortgage statements
python -m beanout sps --input statement.pdf.txt --jsonl --output statement.pdf.jsonl

# CloverLeaf property management statements
python -m beanout clover_leaf --input statement.pdf.txt --jsonl --output statement.pdf.jsonl

# Sheer Value property management statements
python -m beanout sheer_value --input statement.pdf.txt --jsonl --output statement.pdf.jsonl
```

Or output to stdout:

```bash
python -m beanout sps --input statement.pdf.txt --jsonl
```

### Converting JSONL to Beancount

Use the `jsonl_to_bean.py` script:

```bash
# Convert to file
python schema/jsonl_to_bean.py statement.pdf.jsonl statement.pdf.bean

# Convert to stdout
python schema/jsonl_to_bean.py statement.pdf.jsonl
```

### Validating JSONL Files

Use the `validate_jsonl.py` script to check JSONL files against the schema:

```bash
# Basic validation
python schema/validate_jsonl.py statement.pdf.jsonl

# Verbose output
python schema/validate_jsonl.py statement.pdf.jsonl --verbose

# Custom schema
python schema/validate_jsonl.py statement.pdf.jsonl --schema custom.schema.json
```

## JSONL Format

Each line in a `.jsonl` file is a valid JSON object representing a single transaction or error. See `schema/transaction.schema.json` for the full specification.

### Success Case

```json
{
  "ok": true,
  "transaction": {
    "date": "2024-01-15",
    "property": "206-Hoover-Ave",
    "payee_payer": "Tenant",
    "description": "Monthly rent payment",
    "entries": [
      {"account": "Assets:Property-Management:CloverLeaf-PM", "amount_usd": 1500.00},
      {"account": "Income:Rent:206-Hoover-Ave", "amount_usd": -1500.00}
    ],
    "tags": ["rent", "206-hoover-ave", "operations"]
  }
}
```

### Failure Case

```json
{
  "ok": false,
  "error": "Unable to parse date from input",
  "raw_input": "Account,Property / Unit,Date Posted,...",
  "errors": ["Date format not recognized: '01/32/2024'"],
  "notes": "Date appears to be invalid (day 32)"
}
```

## Benefits of JSONL Intermediate Format

1. **Debugging**: Human-readable format makes it easy to inspect parsing results
2. **Validation**: JSON Schema validation catches structural issues before Beancount conversion
3. **Flexibility**: Easy to process with standard JSON tools (jq, Python, etc.)
4. **Pipeline Separation**: Decouples parsing logic from Beancount formatting
5. **Testing**: Golden test files can be version controlled and compared easily

## Schema Notes

- **Transactions Only**: The JSONL format only represents transactions, not balance assertions or other Beancount directives
- **Multiple Postings**: Transactions may have 2 or more postings (entries) as needed for split transactions
- **Property Field**: Required enum field restricts to known properties: `206-Hoover-Ave`, `2943-Butterfly-Palm`, or `Unassigned`
- **Tags**: Optional array of strings for categorization (e.g., `operations`, `mortgage`, property identifiers)

## CI/CD Integration

The GitHub Actions workflow automatically validates all `.jsonl` files in the repository against the schema. See `.github/workflows/ci.yml` for the `jsonl-validation` job.

## Examples

See `schema/examples/sample-transactions.jsonl` for example JSONL objects and `fixtures/golden/` directories for real-world examples from each parser.

## Implementation Details

### Parser Modules

Each parser module (`sps.py`, `clover_leaf.py`, `sheer_value.py`) provides:

- `render_*_file_to_jsonl(filepath)` - Convert a `.pdf.txt` file to JSONL format
- `render_*_text_to_jsonl(text)` - Convert text content to JSONL format

### Shared JSONL Module

The `beanout.jsonl` module provides shared conversion logic:

- `transaction_to_jsonl_object(txn)` - Convert a Beancount Transaction to a JSONL object
- `directives_to_jsonl(directives)` - Convert a list of Beancount directives to JSONL format

### Golden Tests

The `tests/test_jsonl_golden.py` file validates that JSONL output from parsers matches golden files in `fixtures/golden/`.
