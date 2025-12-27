# Plugins

## find_duplicates

Detects likely duplicate transactions within a date window and scores matches.

Configuration example:

```
plugin "plugins.find_duplicates" "
    error_threshold=0.95
    warn_threshold=0.80
    window=3
    tolerance=0.03
    cash_only=true
    property_match=true
"
```

Notes:
- `cash_only=true` compares only `Assets:*` postings for amount/currency matching.
- `property_match=true` suppresses matches when both transactions have different
  property tokens (derived from tags like `#206-hoover-ave` or account segments
  like `Expenses:Management-Fees:206-Hoover-Ave`).
- Warning-level matches are logged but do not fail `bean-check`.
