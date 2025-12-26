# Repository Guidelines

## Project Structure & Module Organization
- `ledger/` contains the Beancount source files. `main.bean` is the entry point and includes `_header.bean`, yearly ledgers (`2022/`–`2026/`), and `_balances.bean` for assertions.
- Year folders (e.g., `ledger/2025/`) hold the primary `_*year*.bean` include plus subfolders for `mortgage/`, `taxes/`, `depreciation/`, and other domain slices.
- `ledger/purchases/` stores property purchase ledgers. Supporting notes live under `_notes/` with Markdown context files.
- Environment metadata is in `devenv.nix`/`devenv.yaml` (Nix-based dev setup).

## Build, Test, and Development Commands
- This repository is ledger data; there is no build step or runtime.
- If you have Beancount installed, validate the ledger with:
  - `bean-check ledger/main.bean` — verifies postings, balances, and plugin constraints.
  - `bean-report ledger/main.bean` — runs reports against the ledger.

## Coding Style & Naming Conventions
- Use Beancount syntax and keep `.bean` files UTF-8 and ASCII-friendly.
- File naming follows descriptive, date/asset-driven patterns: `YYYY_MM_subject.bean` or `####_topic.bean`.
- Use `_`-prefixed files for includes (`_header.bean`, `_2025.bean`).
- Keep account names consistent and hierarchical (e.g., `Assets:Property:206:Escrow`).

## Testing Guidelines
- No automated test framework is configured.
- Treat `bean-check` as the primary validation step before changes.
- Prefer adding balance assertions to `_balances.bean` or year-specific files when introducing new accounts.

## Commit & Pull Request Guidelines
- Recent commit messages are short, imperative phrases (e.g., “Add ledger”, “Small changes”). Keep messages concise and specific.
- PRs should explain the accounting intent (what changed and why), list affected properties/years, and include any supporting notes or documents.

## Security & Configuration Tips
- Ledger data is sensitive. Avoid embedding secrets or personal identifiers outside of the existing account naming patterns.
- Keep notes in `_notes/` and avoid mixing narrative content into `.bean` files unless it is directly relevant to postings.
