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
- Created `ledger/canonical/adjustments/` and moved owner distributions from 2025 operations to `2025-Owner-Distributions.bean`.
- No statement structure created yet.

---

## Next steps (planned)
1. **Create canonical structure** under `ledger/canonical/`:
   - `statements/ManagerName/` (adjustments/ done)
2. **Move existing statement-driven entries** into statement files:
   - Split by statement date and manager as appropriate.
3. **Move non-statement entries** (owner distributions, outside expenses) into `canonical/adjustments/`.
4. **Ensure every canonical file is `YYYY-` prefixed**, so generator includes it for that year.
5. **Run generator** to create `ledger/years/YYYY.bean`.
6. **Verify `ledger/main.bean`** points at `./years/YYYY.bean`.
7. **Run `bean-check ledger/main.bean`** (if available) to validate.

---

## Checklist (migration + validation)

### Migration checklist
- [ ] Create `ledger/canonical/statements/` and `ledger/canonical/adjustments/`.
- [x] Decide manager folder names (e.g., `CloverLeaf`, `SheerValue`) and keep them consistent.
- [ ] Move statement entries into `YYYY-MM-DD-Manager-Statement.bean` files.
- [x] Move owner distributions and outside expenses into `ledger/canonical/adjustments/`.
- [x] Ensure all canonical files use `YYYY-` prefix.
- [ ] Ensure year-specific asset/depreciation/amortization entries are year-prefixed if included in canonical.

### Generation checklist
- [ ] Run `scripts/x/ledger-gen/generate_years.py`.
- [ ] Confirm `ledger/years/YYYY.bean` created for each year present in canonical.
- [ ] Confirm year files have **section headers** and **lexicographic ordering** of includes.
- [ ] Confirm `ledger/main.bean` year include block points to `./years/YYYY.bean`.

### Validation checklist
- [ ] `bean-check ledger/main.bean` (if available).
- [ ] Spot-check a year file: includes all expected statements and adjustments.
- [ ] Ensure no duplicate includes and no missing statement dates.
- [ ] Confirm ignored files (`_notes`, `draft-*`) are not included.

---

## Notes
- This approach optimizes for **source-of-truth accuracy** (statements) rather than property/file boundaries.
- Tags remain the primary way to filter by property (`#206-hoover-ave`, `#2943-butterfly-palm`) and domain (`#operations`, `#distributions`, etc.).
- The generator is intentionally filename-driven; no Beancount parsing required.
