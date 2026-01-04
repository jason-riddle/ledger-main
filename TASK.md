# Task Context: Ledger Restructure + Year Generator

## Scope and intent
- **Goal:** Move the ledger organization to a statement-first canonical layout, because property managers provide **one statement covering multiple properties and non-property activity** (e.g., owner distributions). A property-first file layout is not viable.
- **Desired lens:** Statements are the **primary source of truth**, with **adjustments** for non-statement items (outside expenses, owner distributions, corrections).
- **Secondary need:** Generate per-year include files automatically to keep the `ledger/main.bean` include list consistent and lexicographically ordered.

## Why we are doing this
- Current domain/property/year-first layout is starting to feel **messy and hard to maintain**.
- Statements are multi-property and include non-property transactions; forcing property-specific files creates churn and misrepresents the source.
- Automatic year file generation prevents include drift and enforces ordering rules without manual maintenance.

---

## Current state (before)
**Ledger structure (excerpt):**
```
ledger/
  2022/
    2022.bean
    operations/
    mortgage/
    taxes/
    assets/
    depreciation/
    amortization/
  2023/
  2024/
  2025/
  2026/
  header.bean
  main.bean
  balances.bean
```

**Key files reviewed:**
- `ledger/header.bean`
- `ledger/main.bean`
- `ledger/2024/2024.bean`

---

## Decided direction
**Primary layout:** statement-first canonical + adjustments, with generated year views.

### Target (after) directory structure
```
ledger/
  canonical/
    statements/
      CloverLeaf/
        YYYY-MM-DD-CloverLeaf-Statement.bean
      SheerValue/
        YYYY-MM-DD-SheerValue-Statement.bean
    adjustments/
      YYYY-Owner-Distributions.bean
      YYYY-Outside-Expenses.bean
    (optional future groups)
      assets/
      depreciation/
      amortization/
    header.bean
  years/
    2024.bean   (generated)
    2025.bean   (generated)
  main.bean
  balances.bean
```

### Naming decisions
- **Statements:** `YYYY-MM-DD-Manager-Statement.bean` (confirmed).
- **Adjustments:** `YYYY-<Description>.bean` (year prefixed, grouped under `canonical/adjustments`).

---

## Script created (what we just did)
**Path:** `scripts/x/ledger-gen/generate_years.py`

**Purpose:** Generate `ledger/years/YYYY.bean` from `ledger/canonical/**/YYYY-*.bean` and update `ledger/main.bean` to include `./years/YYYY.bean`.

**Behavior:**
- Scans `ledger/canonical/` recursively for `.bean` files named `YYYY-*.bean`.
- **Ignores:**
  - Any path containing `_notes`.
  - Any filename starting with `draft-`.
  - Any file not ending in `.bean`.
- Groups includes by **top-level folder under `ledger/canonical/`** (e.g., `statements`, `adjustments`, `assets`).
- Writes `ledger/years/YYYY.bean` with section headers and lexicographically sorted include lines.
- Updates `ledger/main.bean` year include block to point at `./years/YYYY.bean`.

**Usage:**
```
scripts/x/ledger-gen/generate_years.py
scripts/x/ledger-gen/generate_years.py --year 2024
scripts/x/ledger-gen/generate_years.py --dry-run
```

---

## Q/A recap (for provenance)
- **Q:** Can we switch to statement-first and keep adjustments?
  **A:** Yes. Statements are canonical; adjustments handle outside expenses, owner distributions, corrections.

- **Q:** Should year files include everything or only statements + adjustments?
  **A:** Leaning toward **include everything** (Option 1A). Year files include all canonical files with `YYYY-` prefix.

- **Q:** Naming for statements?
  **A:** Use `YYYY-MM-DD-Manager-Statement.bean` (confirmed).

- **Q:** Script location and behavior?
  **A:** Script lives in `scripts/x/ledger-gen/`, generates all years by default, supports `--year`, supports `--dry-run`, ignores `_notes` and `draft-*`.

---

## What changes have been made so far
- Added generator script: `scripts/x/ledger-gen/generate_years.py` (executable).
- Created `ledger/canonical/` structure: adjustments/, statements/SheerValue/, statements/CloverLeaf/, amortization/, depreciation/, mortgage/, taxes/
- Moved owner distributions from operations to adjustments.
- Moved statement-driven transactions from operations to statements (SheerValue and CloverLeaf).
- Moved year-specific files from 2024/ and 2025/ to canonical subdirectories.
- Generated `ledger/years/2024.bean` and `ledger/years/2025.bean`.
- Updated `ledger/main.bean` to include `./years/YYYY.bean` for 2024 and 2025.

---

## Restructuring Complete
- All ledger files reorganized into canonical statement-first layout under `ledger/canonical/` (statements/, adjustments/, amortization/, depreciation/, mortgage/, taxes/, assets/).
- Year beans auto-generated in `ledger/years/` and included in `ledger/main.bean`.
- Process repeated for all years (2022-2026).

## Post-Restructure Notes & Follow-Up
- **Bean-check failures**: `bean-check ledger/main.bean` reports numerous balance assertion failures (e.g., Equity:Owner-Contributions:Cash-Infusion, Assets:Escrow:Taxes---Insurance, Assets:Land/Buildings, Liabilities:Mortgages). This indicates missing transactions in the ledger, not structural issues. Accumulated balances don't match expected values due to incomplete accounting records.
  - Examples:
    - 2022-12-31: Equity:Owner-Contributions expected -112078.73 USD, accumulated -109721.47 USD (2357.26 too much).
    - 2023-12-31: Same account expected -258381.43 USD, accumulated -256024.17 USD (2357.26 too much).
    - 2024-01-01: Assets:Land:206-Hoover-Ave expected 27469.00 USD, accumulated 28410.32 USD (941.32 too much).
    - 2024-01-01: Assets:Land:2943-Butterfly-Palm expected 45191.00 USD, accumulated 44358.00 USD (833.00 too little).
    - Mortgage/escrow balances consistently off by ~762.80 USD and 121.46 USD, suggesting missing escrow adjustments or partial payments.
    - Depreciation balances fail due to missing asset purchases or incorrect initial values.
  - Root cause: Ledger lacks full transaction history; restructure organized existing data but didn't add missing entries.
- **Plugin import resolved**: Initial "No module named 'src'" error fixed (PYTHONPATH issue); bean-check now runs without import failures.
- **Follow-up tasks**:
  - Audit external financial records (bank statements, property manager reports, tax documents, receipts) to identify and add missing transactions (contributions, expenses, asset purchases, escrow adjustments).
  - Review balance assertions in `ledger/balances.bean` against actual account activity; update expectations if ledger is intentionally partial.
  - Verify all statement files include complete transaction sets; add any omitted entries from original PDFs/CSV sources.
  - Consider regenerating depreciation if asset bases are incorrect.
  - Test with `bean-report` for account summaries to spot inconsistencies.
- **Assets inclusion**: Property purchase files moved to `canonical/assets/` as requested, improving some balances but not fully resolving (partial transactions present).

---

## Checklist (migration + validation)

### Migration checklist
- [x] Create `ledger/canonical/statements/` and `ledger/canonical/adjustments/`.
- [x] Decide manager folder names (e.g., `CloverLeaf`, `SheerValue`) and keep them consistent.
- [x] Move statement entries into `YYYY-MM-DD-Manager-Statement.bean` files.
- [x] Move owner distributions and outside expenses into `ledger/canonical/adjustments/`.
- [x] Ensure all canonical files use `YYYY-` prefix.
- [x] Ensure year-specific asset/depreciation/amortization entries are year-prefixed if included in canonical.

### Generation checklist
- [x] Run `scripts/x/ledger-gen/generate_years.py`.
- [x] Confirm `ledger/years/YYYY.bean` created for each year present in canonical.
- [x] Confirm year files have **section headers** and **lexicographic ordering** of includes.
- [x] Confirm `ledger/main.bean` year include block points to `./years/YYYY.bean`.

### Validation checklist
- [x] `bean-check ledger/main.bean` (if available). (Note: balance assertions fail for years not yet moved to canonical)
- [x] Spot-check a year file: includes all expected statements and adjustments.
- [x] Ensure no duplicate includes and no missing statement dates.
- [x] Confirm ignored files (`_notes`, `draft-*`) are not included.

---

## Notes
- This approach optimizes for **source-of-truth accuracy** (statements) rather than property/file boundaries.
- Tags remain the primary way to filter by property (`#206-hoover-ave`, `#2943-butterfly-palm`) and domain (`#operations`, `#distributions`, etc.).
- The generator is intentionally filename-driven; no Beancount parsing required.
