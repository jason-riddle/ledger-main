# JSONL Processing Pipeline - Implementation Summary

## Overview
This PR implements a complete JSONL processing pipeline for converting property management statement text files into Beancount format. The pipeline adds a structured intermediate format (JSONL) between text parsing and Beancount generation.

## Pipeline Architecture

```
┌──────────┐      ┌────────────┐      ┌────────────┐
│ .pdf.txt │──────▶│ .pdf.jsonl │──────▶│ .pdf.bean  │
└──────────┘      └────────────┘      └────────────┘
     │                   │                    │
   Parse            Validate              Convert
  Statement          Schema             to Beancount
```

## Changes Made

### 1. Core JSONL Module (`src/beanout/jsonl.py`)
- `transaction_to_jsonl_object()` - Converts Beancount Transaction to JSON object
- `directives_to_jsonl()` - Converts list of directives to JSONL format
- Handles property extraction from tags/accounts
- Preserves all transaction metadata (date, payee, description, entries, tags)

### 2. Parser Updates
Extended all three parsers with JSONL output capability:
- **SPS Parser** (`src/beanout/sps.py`)
  - `render_sps_text_to_jsonl()`
  - `render_sps_file_to_jsonl()`
- **CloverLeaf Parser** (`src/beanout/clover_leaf.py`)
  - `render_clover_leaf_text_to_jsonl()`
  - `render_clover_leaf_file_to_jsonl()`
- **Sheer Value Parser** (`src/beanout/sheer_value.py`)
  - `render_sheer_value_text_to_jsonl()`
  - `render_sheer_value_file_to_jsonl()`

### 3. CLI Enhancement (`src/beanout/cli.py`)
- Added `--jsonl` flag to all parser subcommands
- Refactored command handling to reduce code duplication
- Unified error handling and output writing

### 4. Schema Updates
- **`schema/transaction.schema.json`**
  - Changed entries constraint from exactly 2 to minimum 2 (allows multi-leg transactions)
- **`schema/README.md`**
  - Updated documentation to reflect schema changes

### 5. Testing Infrastructure
- **Golden Files** - Generated `.pdf.jsonl` for all fixtures:
  - `fixtures/golden/sps/` (2 files)
  - `fixtures/golden/clover-leaf/` (1 file)
  - `fixtures/golden/sheer-value/` (3 files)
- **Test Suite** (`tests/test_jsonl_golden.py`)
  - Parameterized helper function to reduce duplication
  - Tests all three parsers against golden files
  - JSON-aware comparison (order-independent)

### 6. CI/CD Integration
- **GitHub Actions** (`.github/workflows/ci.yml`)
  - Added `jsonl-validation` job
  - Automatically validates all `.jsonl` files against schema
  - Proper security permissions (`contents: read`)

### 7. Documentation
- **`JSONL_PIPELINE.md`** - Comprehensive documentation:
  - Pipeline overview
  - Usage examples
  - JSONL format specification
  - Benefits and implementation details
  - CI/CD integration notes

### 8. Configuration
- **`pyproject.toml`**
  - Lowered Python requirement from >=3.13 to >=3.12

## Usage Examples

### Generate JSONL
```bash
python -m beanout sps --input statement.pdf.txt --jsonl --output statement.pdf.jsonl
```

### Validate JSONL
```bash
python schema/validate_jsonl.py statement.pdf.jsonl
```

### Convert to Beancount
```bash
python schema/jsonl_to_bean.py statement.pdf.jsonl statement.pdf.bean
```

## Quality Assurance

### Tests Passing
- ✅ All original golden tests (Bean format)
- ✅ New JSONL golden tests
- ✅ End-to-end pipeline test
- ✅ Schema validation

### Code Quality
- ✅ Ruff linting (no errors)
- ✅ CodeQL security scan (no alerts)
- ✅ Code review feedback addressed
- ✅ Reduced code duplication through refactoring

### Security
- ✅ Explicit workflow permissions
- ✅ No vulnerability alerts
- ✅ Input validation via JSON schema

## Files Changed
- **Created**: 8 files (1 module, 1 test, 6 golden files)
- **Modified**: 9 files (3 parsers, 1 CLI, 1 workflow, 2 schema, 2 docs)
- **Total**: +259 lines, -43 lines

## Benefits

1. **Debugging** - Human-readable JSON format for inspection
2. **Validation** - Structured schema checking before conversion
3. **Flexibility** - Easy processing with standard tools (jq, Python, etc.)
4. **Testing** - Version-controlled golden files for regression testing
5. **Pipeline Separation** - Independent stages for easier maintenance
6. **Documentation** - Clear intermediate format specification

## Backward Compatibility

✅ **Fully backward compatible** - All existing functionality preserved:
- Direct `.pdf.txt` → `.pdf.bean` conversion still works
- All original tests pass
- No breaking changes to existing APIs

## Next Steps (Future Work)
- Consider adding more detailed error reporting in JSONL
- Potential support for balance assertions in JSONL format
- Add JSONL merge/split utilities if needed
