# Beanout Parser Refactoring

This document describes the refactoring of the `src/beanout/` parser code to reduce duplication and improve organization.

## Overview

The refactoring extracts common functionality into shared utility modules while maintaining backward compatibility. Three parsers (SPS, Ally Bank, Chase) have been fully refactored following a format-specific pattern, and the infrastructure is in place for refactoring the remaining parsers.

## Directory Structure

```
src/beanout/
├── common/                      # Shared utilities
│   ├── __init__.py
│   ├── amounts.py              # Amount parsing (parse_amount, negate, etc.)
│   ├── beancount_helpers.py    # Beancount directive creation
│   ├── io.py                   # File I/O utilities
│   ├── rendering.py            # Output rendering (Beancount, JSONL)
│   └── ofx.py                  # OFX/QFX parsing utilities
├── entities/                   # Entity-specific parsers
│   ├── __init__.py
│   ├── sps/                    # Example: Refactored (PDF format)
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration dataclass
│   │   ├── pdf_parser.py      # PDF format parser
│   │   └── parser.py          # Main public API
│   ├── ally_bank/              # Example: Refactored (CSV + QFX)
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration dataclass
│   │   ├── csv_parser.py      # CSV format parser
│   │   ├── qfx_parser.py      # QFX format parser
│   │   └── parser.py          # Main public API
│   ├── chase/                  # Example: Refactored (CSV + QFX)
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration dataclass
│   │   ├── csv_parser.py      # CSV format parser
│   │   ├── qfx_parser.py      # QFX format parser
│   │   └── parser.py          # Main public API
│   ├── schwab/                 # To be refactored (JSON + XML)
│   ├── fidelity/               # To be refactored (CSV)
│   ├── sheer_value/            # To be refactored (PDF)
│   └── clover_leaf/            # To be refactored (PDF + CSV + JSON)
├── sps.py                      # Backward compatibility wrapper (re-exports)
├── ally_bank.py                # Backward compatibility wrapper (re-exports)
├── chase.py                    # Backward compatibility wrapper (re-exports)
└── ...                         # Other parsers (to be refactored)
```

## New Organization Pattern

Each entity package follows this structure:

```
src/beanout/entities/{entity}/
├── __init__.py                 # Package documentation, re-exports from parser.py
├── config.py                   # Configuration dataclass for account settings
├── {format}_parser.py          # Format-specific parser(s)
│   ├── csv_parser.py          # For CSV format
│   ├── qfx_parser.py          # For QFX/OFX format
│   ├── pdf_parser.py          # For PDF text format
│   ├── json_parser.py         # For JSON format
│   └── xml_parser.py          # For XML format
└── parser.py                   # Main public API module
```

### Why This Organization?

1. **Config in separate file**: 
   - Easy to find and modify account settings
   - No need to navigate through parsing logic
   - Clear separation between configuration and code

2. **Format-specific parsers**:
   - Each format (CSV, QFX, PDF, JSON, XML) has its own focused file
   - Easier to understand each format independently
   - Clear separation of concerns - no mixing of unrelated parsing logic
   - Easier to test each format in isolation
   - When adding support for a new format, just add a new `{format}_parser.py`

3. **Main parser.py as public API**:
   - Single entry point for all formats
   - Orchestrates format-specific parsers
   - Provides clean, format-agnostic function names
   - Handles file I/O using shared utilities

4. **Smaller, focused files**:
   - Ally Bank: 271 lines → 4 files averaging ~87 lines each
   - Chase: 273 lines → 4 files averaging ~85 lines each
   - SPS: 386 lines → 3 files averaging ~135 lines each (only 1 format)
   - Easier to navigate and understand
   - Reduced cognitive load when making changes

## Shared Utilities

### amounts.py

Provides amount parsing and manipulation:

- `parse_amount(amount_str)` - Parse string amounts (handles $, commas, parentheses)
- `parse_optional_amount(value)` - Parse optional/nullable amounts
- `ensure_decimal(value)` - Ensure value is a Decimal
- `negate(value)` - Negate with zero normalization

### beancount_helpers.py

Provides helpers for creating Beancount directives:

- `create_posting(account, amount, currency)` - Create a posting
- `create_transaction(date, flag, payee, narration, postings, ...)` - Create a transaction
- `create_balance(date, account, amount, currency)` - Create a balance assertion
- `sort_postings(postings)` - Sort postings (negative first, then positive)
- `build_two_posting_transaction(...)` - Convenience for simple transactions

### io.py

Provides file I/O utilities:

- `validate_file_extension(filepath, expected)` - Validate file extension
- `read_text_file(filepath, encoding)` - Read text file
- `read_binary_file(filepath)` - Read binary file
- `render_file_generic(filepath, extension, render_func)` - Generic text file renderer
- `render_binary_file_generic(filepath, extension, render_func)` - Generic binary file renderer

### rendering.py

Provides output rendering:

- `render_to_beancount(entries)` - Render to Beancount text
- `render_to_jsonl(entries)` - Render to JSONL format

### ofx.py

Provides OFX/QFX parsing utilities:

- `parse_ofx_data(data)` - Parse OFX data
- `build_ofx_narration(tx_type, name, memo, fallback)` - Build narration from OFX fields

## Example: Ally Bank Refactoring

The Ally Bank parser demonstrates the format-specific pattern for entities with multiple formats:

**Before** (old `ally_bank.py`):
- 271 lines with CSV and QFX parsing mixed together
- Duplicated utility functions
- Mixed concerns (parsing, I/O, amount handling, rendering)
- Difficult to test individual formats

**After**:
- `src/beanout/entities/ally_bank/config.py`: 17 lines - just the config
- `src/beanout/entities/ally_bank/csv_parser.py`: 122 lines - pure CSV parsing logic
- `src/beanout/entities/ally_bank/qfx_parser.py`: 96 lines - pure QFX parsing logic
- `src/beanout/entities/ally_bank/parser.py`: 115 lines - clean public API
- `src/beanout/ally_bank.py`: Simple re-export wrapper for backward compatibility
- Uses shared utilities for all common operations
- Each format can be tested independently
- Easier to maintain and extend

## Usage Examples

### Using Format-Specific Parsers Directly

```python
from beanout.entities.ally_bank import csv_parser, qfx_parser
from beanout.entities.ally_bank.config import AllyBankConfig

# Parse CSV
csv_text = "..."
entries = csv_parser.parse_csv_text(csv_text)
beancount_output = csv_parser.render_csv_text(csv_text)

# Parse QFX
qfx_data = b"..."
entries = qfx_parser.parse_qfx_data(qfx_data)
beancount_output = qfx_parser.render_qfx_data(qfx_data)

# Custom config
config = AllyBankConfig(account_cash="Assets:Bank:Ally")
entries = csv_parser.parse_csv_text(csv_text, config)
```

### Using Main Parser API

```python
from beanout.entities.ally_bank import parser

# File rendering (format detected by extension)
beancount_output = parser.render_ally_bank_csv_file("statement.csv")
jsonl_output = parser.render_ally_bank_csv_file_to_jsonl("statement.csv")

qfx_output = parser.render_ally_bank_qfx_file("statement.qfx")
```

### Creating a Transaction with Shared Utilities

```python
from beanout.common import amounts, beancount_helpers

# Parse amounts
principal = amounts.parse_amount("$1,234.56")
interest = amounts.parse_amount("$789.12")

# Create postings
postings = [
    beancount_helpers.create_posting("Assets:Cash", amounts.negate(principal), "USD"),
    beancount_helpers.create_posting("Liabilities:Mortgage", principal, "USD"),
]

# Create transaction
txn = beancount_helpers.create_transaction(
    date=datetime.date(2024, 1, 1),
    flag="*",
    payee="Bank",
    narration="Mortgage Payment",
    postings=postings,
    tags={"mortgage"},
)
```

## Testing

All shared utilities have test coverage in `tests/test_common_utilities.py`.

To run tests:
```bash
uv run pytest tests/test_common_utilities.py -v
uv run pytest tests/test_ally_bank_golden.py -v  # Test Ally Bank
uv run pytest tests/test_chase_golden.py -v       # Test Chase
uv run pytest tests/test_sps_golden.py -v         # Test SPS
```

## Backward Compatibility

All existing parser files maintain their public API by re-exporting from the refactored versions. No breaking changes for users.

Example from `ally_bank.py`:
```python
from beanout.entities.ally_bank.parser import (
    AllyBankConfig,
    parse_ally_bank_csv_text,
    render_ally_bank_csv_file,
    # ... other exports
)
```

## Future Work

The following parsers can be refactored using the same pattern:

1. **CloverLeaf** (719 lines) - Most complex, needs 3 format parsers:
   - `pdf_parser.py` for PDF text statements
   - `csv_parser.py` for CSV ledger files
   - `json_parser.py` for JSON ledger files

2. **Schwab** (280 lines) - Needs 2 format parsers:
   - `json_parser.py` for JSON statements
   - `xml_parser.py` for XML statements

3. **Fidelity** (200 lines) - Simple, needs 1 format parser:
   - `csv_parser.py` for CSV statements

4. **Sheer Value** (413 lines) - Needs 1 format parser:
   - `pdf_parser.py` for PDF text statements

## Guidelines for Refactoring Parsers

When refactoring a parser:

1. **Create entity package** under `src/beanout/entities/{entity_name}/`

2. **Extract config** to `config.py`:
   ```python
   @dataclasses.dataclass(frozen=True)
   class EntityConfig:
       account_cash: str = "Assets:Cash"
       # ... other settings
   ```

3. **Create format-specific parsers** (one file per format):
   - `csv_parser.py`, `qfx_parser.py`, `pdf_parser.py`, etc.
   - Each should have: `parse_{format}_text/data()`, `render_{format}_text/data()`, `render_{format}_text/data_to_jsonl()`
   - Use shared utilities from `common/`

4. **Create main parser.py**:
   - Re-export config
   - Provide format-agnostic public API functions
   - Handle file I/O using `io.render_file_generic()` or `io.render_binary_file_generic()`

5. **Update original file** as backward compatibility wrapper:
   - Import and re-export everything from `entities/{entity}/parser.py`

6. **Add/update tests** to ensure functionality is preserved

7. **Run all tests** to verify nothing breaks

## Benefits

- **Reduced duplication**: Common utilities in one place
- **Easier testing**: Shared utilities and individual formats can be tested independently
- **Better organization**: Clear separation by format and concern
- **Easier maintenance**: Changes to common logic need only one update
- **Backward compatible**: Existing code continues to work
- **Foundation for future work**: Pattern established for remaining parsers
- **Smaller files**: Easier to navigate and understand
- **Focused responsibilities**: Each file has a single, clear purpose
