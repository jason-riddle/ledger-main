# Repository Guidelines

## Project Structure & Module Organization
- `ledger/` contains the Beancount source files. `main.bean` is the entry point and includes `_header.bean`, yearly ledgers (`2022/`–`2026/`), and `_balances.bean` for assertions.
- Year folders (e.g., `ledger/2025/`) hold the primary `_*year*.bean` include plus subfolders for `mortgage/`, `taxes/`, `depreciation/` (with `buildings/` and `improvements/`), `assets/` (with `buildings/` and `improvements/`), `operations/`, and other domain slices.
- Supporting notes live under `_notes/` with Markdown context files.
- Environment metadata is in `devenv.nix`/`devenv.yaml` (Nix-based dev setup).

## Build, Test, and Development Commands
- This repository is ledger data; there is no build step or runtime.
- Before making any code changes, always read `ledger/_header.bean` first.
- If you have Beancount installed, validate the ledger with:
  - `bean-check ledger/main.bean` — verifies postings, balances, and plugin constraints.
  - `bean-report ledger/main.bean` — runs reports against the ledger.
- Plugin tests are runnable with `uv` (scripts include their own dependencies), e.g.:
  - `UV_PYTHON=/nix/store/3lll9y925zz9393sa59h653xik66srjb-python3-3.13.9/bin/python3.13 uv run ledger/plugins/tests/test_find_duplicates.py -q`.

## Coding Style & Naming Conventions
- Use Beancount syntax and keep `.bean` files UTF-8 and ASCII-friendly.
- Python code follows the Google Python Style Guide; see `PYTHON_STYLE_GUIDE.md`.
- File naming follows descriptive, date/asset-driven patterns:
  - Year includes: `YYYY.bean`.
  - Operations summary: `YYYY-Operations-All.bean`.
  - Statements (manager-specific when needed): `YYYY-VENDOR-PROPERTY-Statement.bean` (stored in `operations/`).
  - Operations transactions: `YYYY-PROPERTY-Transactions.bean` (stored in `operations/`).
  - Buildings (property purchases): `YYYY-PROPERTY-YYYY-MM-DD-Property-Purchase.bean`.
  - Improvements: `YYYY-PROPERTY-YYYY-MM-DD-ASSET.bean`.
  - Depreciation/amortization: `YYYY-PROPERTY-YYYY-MM-DD-ASSET.bean`.
  - Mortgage/escrow: `YYYY-PROPERTY-Mortgage-Payments.bean`, `YYYY-PROPERTY-Escrow-Payouts.bean`.
  - Taxes: `YYYY-PROPERTY-Taxes.bean`.
  - `PROPERTY` is hyphenated (`206-Hoover-Ave`) and vendor casing is `SheerValue` / `CloverLeaf` in statement filenames when used.
- Directory names are lowercase, domain-oriented (e.g., `mortgage/`, `taxes/`, `depreciation/`, `depreciation/buildings/`, `depreciation/improvements/`, `assets/`, `assets/buildings/`, `assets/improvements/`, `operations/`).
- Use `_`-prefixed files for includes (`_header.bean`), but year files are `YYYY.bean`.
- In yearly `YYYY.bean` files, alphabetize the section headers and keep every line within a section in strict lexicographic order (including `include` lines and `;; TODO:` notes).
- Keep account names consistent and hierarchical, with date-stamped subaccounts for fixed assets and accumulated depreciation (e.g., `Assets:Fixed-Assets:2943-Butterfly-Palm:Improvements:2023-02-17-Water-Heater`).
- For multi-line transactions, list negative postings first, then positive postings.
- `YYYY-Operations-All.bean` should include the per-property `YYYY-PROPERTY-Transactions.bean` files.
- Tag conventions for transactions:
  - Buildings transactions: `#buildings`.
  - Improvements transactions (including loan-cost amortization entries in improvements): `#improvements`.
  - Escrow-related transactions: `#escrow` and `#mortgage`.
  - Operations transactions: `#operations`.
- Transaction header ordering: alphabetize tags (`#...`) first, then alphabetize links (`^...`), with tags placed before links.
- Comment styling:
  - File headers use a 3-line double-semicolon block with uppercase titles and hyphenated property names, followed by a blank line. Format:
    - Line 1: `;;`
    - Line 2: `;; YEAR/ALL - DOMAIN - PROPERTY - DETAIL` (PROPERTY and DETAIL are optional; use `ALL` where appropriate)
    - Line 3: `;;`
  - Use single-semicolon `;` for explanatory notes and inline context; keep alignment compact and ASCII-friendly.
  - TODOs use `;; TODO:` and live near the top of files or sections they apply to.

## Testing Guidelines
- No shared automated test framework is configured, but some tests are standalone `uv` scripts.
- Treat `bean-check` as the primary validation step before changes.
- Prefer adding balance assertions to `_balances.bean` or year-specific files when introducing new accounts. Because `leafonly` is enabled, assertions must target leaf accounts.

## Plugin Notes
- `ledger/plugins/find_duplicates.py` supports a `cash_only=true` flag to compare only `Assets:*` postings for amount/currency matching. Warning-level matches are logged and do not fail `bean-check`.
- `ledger/plugins/find_duplicates.py` supports `property_match=true` to suppress duplicate matches when both transactions include different property tokens (tags like `#206-hoover-ave` or account segments like `...:206-Hoover-Ave`).

## Commit & Pull Request Guidelines
- Recent commit messages are short, imperative phrases (e.g., “Add ledger”, “Small changes”). Keep messages concise and specific.
- PRs should explain the accounting intent (what changed and why), list affected properties/years, and include any supporting notes or documents.
- Note: Pre-commit hooks may need escalated permissions to write cache files (e.g., under `~/.cache/pre-commit`). If a commit fails with a PermissionError, rerun the commit with the required permissions; also mark scripts with shebangs as executable when appropriate to satisfy hook checks.

## Security & Configuration Tips
- Ledger data is sensitive. Avoid embedding secrets or personal identifiers outside of the existing account naming patterns.
- Keep notes in `_notes/` and avoid mixing narrative content into `.bean` files unless it is directly relevant to postings.
