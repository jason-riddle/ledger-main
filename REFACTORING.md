# Beanout Parser Refactoring

This document describes the refactoring of the `src/beanout/` parser code to reduce duplication and improve organization.

## Overview

The refactoring extracts common functionality into shared utility modules while maintaining backward compatibility. The SPS parser has been fully refactored as an example, and the infrastructure is in place for refactoring the remaining parsers.

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
│   ├── sps/                    # Example: Fully refactored
│   │   ├── __init__.py
│   │   └── parser.py          # Clean parser using shared utilities
│   ├── ally_bank/
│   ├── chase/
│   ├── schwab/
│   ├── fidelity/
│   ├── sheer_value/
│   └── clover_leaf/
├── sps.py                      # Backward compatibility wrapper (re-exports)
├── ally_bank.py                # Original implementation (to be refactored)
├── chase.py                    # Original implementation (to be refactored)
└── ...                         # Other parsers
```

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
- `render_file_generic(filepath, extension, render_func)` - Generic file renderer

### rendering.py

Provides output rendering:

- `render_to_beancount(entries)` - Render to Beancount text
- `render_to_jsonl(entries)` - Render to JSONL format

### ofx.py

Provides OFX/QFX parsing utilities:

- `parse_ofx_data(data)` - Parse OFX data
- `build_ofx_narration(tx_type, name, memo, fallback)` - Build narration from OFX fields

## Example: SPS Parser Refactoring

The SPS parser demonstrates the refactoring pattern:

**Before** (old `sps.py`):
- 452 lines with duplicated utility functions
- Mixed concerns (parsing, I/O, amount handling, rendering)
- Difficult to test individual components

**After**:
- `src/beanout/entities/sps/parser.py`: 394 lines of pure parsing logic
- Uses shared utilities for all common operations
- `src/beanout/sps.py`: Simple re-export wrapper for backward compatibility
- Easier to test and maintain

## Usage Examples

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

### File I/O with Shared Utilities

```python
from beanout.common import io, rendering

def render_my_file(filepath: str) -> str:
    return io.render_file_generic(
        filepath,
        ".txt",
        lambda text: parse_and_render(text),
    )

def parse_and_render(text: str) -> str:
    entries = parse_my_format(text)
    return rendering.render_to_beancount(entries)
```

## Testing

All shared utilities have test coverage in `tests/test_common_utilities.py`.

To run tests:
```bash
uv run pytest tests/test_common_utilities.py -v
```

## Backward Compatibility

All existing parser files maintain their public API by re-exporting from the refactored versions or keeping the original implementation. No breaking changes for users.

Example from `sps.py`:
```python
from beanout.entities.sps.parser import (
    SPSConfig,
    parse_sps_text,
    render_sps_file,
    # ... other exports
)
```

## Future Work

The following parsers can be refactored using the same pattern as SPS:

1. **Banking parsers** (ally_bank, chase, schwab):
   - Share OFX parsing logic via `common/ofx.py`
   - Extract common CSV parsing patterns
   
2. **Property management parsers** (sheer_value, clover_leaf):
   - Share PDF text parsing patterns
   - Extract common property/account mapping logic

3. **Brokerage parsers** (fidelity):
   - Extract CSV parsing patterns

## Guidelines for Refactoring Parsers

When refactoring a parser:

1. **Keep the original file** as a backward compatibility wrapper
2. **Create entity package** under `src/beanout/entities/{entity_name}/`
3. **Extract parsing logic** to `parser.py` in the entity package
4. **Use shared utilities** from `common/` instead of duplicating code
5. **Re-export from original file** to maintain API compatibility
6. **Add/update tests** to ensure functionality is preserved
7. **Run all tests** to verify nothing breaks

## Benefits

- **Reduced duplication**: Common utilities in one place
- **Easier testing**: Shared utilities can be tested independently
- **Better organization**: Clear separation of concerns
- **Easier maintenance**: Changes to common logic need only one update
- **Backward compatible**: Existing code continues to work
- **Foundation for future work**: Pattern established for remaining parsers
