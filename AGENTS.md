# Repository Guidelines

## Project Structure & Module Organization
- `ledger/` contains the Beancount source files. `main.bean` is the entry point and includes `_header.bean`, yearly ledgers (`2022/`–`2026/`), and `_balances.bean` for assertions.
- Year folders (e.g., `ledger/2025/`) hold the primary `_*year*.bean` include plus subfolders for `mortgage/`, `taxes/`, `depreciation/`, `assets/`, and other domain slices.
- `ledger/purchases/` stores property purchase ledgers. Supporting notes live under `_notes/` with Markdown context files.
- Environment metadata is in `devenv.nix`/`devenv.yaml` (Nix-based dev setup).

## Build, Test, and Development Commands
- This repository is ledger data; there is no build step or runtime.
- If you have Beancount installed, validate the ledger with:
  - `bean-check ledger/main.bean` — verifies postings, balances, and plugin constraints.
  - `bean-report ledger/main.bean` — runs reports against the ledger.

## Coding Style & Naming Conventions
- Use Beancount syntax and keep `.bean` files UTF-8 and ASCII-friendly.
- File naming follows descriptive, date/asset-driven patterns: `YYYY-MM-Property-Asset-Detail.bean` for asset/depreciation files and `_YYYY.bean` for yearly includes.
- Use `_`-prefixed files for includes (`_header.bean`, `_2025.bean`).
- Keep account names consistent and hierarchical, with date-stamped subaccounts for fixed assets and accumulated depreciation (e.g., `Assets:Fixed-Assets:2943-Butterfly-Palm:Improvements:2023-02-17-Water-Heater`).
- For multi-line transactions, list negative postings first, then positive postings.
- Comment styling:
  - File headers use double-semicolon blocks with uppercase titles and hyphenated property names (e.g., `;; 2024 - DEPRECIATION - 2943-BUTTERFLY-PALM - BUILDING`), followed by a blank line.
  - Use single-semicolon `;` for explanatory notes and inline context; keep alignment compact and ASCII-friendly.
  - TODOs use `;; TODO:` and live near the top of files or sections they apply to.

## Testing Guidelines
- No automated test framework is configured.
- Treat `bean-check` as the primary validation step before changes.
- Prefer adding balance assertions to `_balances.bean` or year-specific files when introducing new accounts. Because `leafonly` is enabled, assertions must target leaf accounts.

## Commit & Pull Request Guidelines
- Recent commit messages are short, imperative phrases (e.g., “Add ledger”, “Small changes”). Keep messages concise and specific.
- PRs should explain the accounting intent (what changed and why), list affected properties/years, and include any supporting notes or documents.

## Security & Configuration Tips
- Ledger data is sensitive. Avoid embedding secrets or personal identifiers outside of the existing account naming patterns.
- Keep notes in `_notes/` and avoid mixing narrative content into `.bean` files unless it is directly relevant to postings.
