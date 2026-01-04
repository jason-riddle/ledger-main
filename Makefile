.PHONY: uv-sync test plugins-test check query query-cmd accounts expenses pre-commit

BEANQUERY ?= /nix/store/kafcag27b7a9mw09625kjk2apag2shib-python3.13-beanquery-0.2.0/bin/bean-query
BEANQUERY_PYTHONPATH ?= .:src:/home/jason/.cache/uv/archive-v0/8hCQXdtc37UJC8cz_DEbP

uv-sync:
	uv sync --dev

test:
	uv run pytest -q

plugins-test:
	uv run src/plugins/tests/test_find_duplicates.py -q

check:
	uv run bean-check ledger/main.bean

query:
	uv run python scripts/bin/bean-query-nohistory.py ledger/main.bean

query-cmd:
	@if [ -z "$(QUERY)" ]; then echo "Usage: make query-cmd QUERY='select ...'"; exit 2; fi
	uv run python scripts/bin/bean-query-nohistory.py ledger/main.bean "$(QUERY)"

accounts:
	2>/dev/null PYTHONPATH=$(BEANQUERY_PYTHONPATH) $(BEANQUERY) --format csv ledger/main.bean \
		"SELECT DISTINCT account, open_date(account) AS open_date, close_date(account) AS close_date, close_date(account) IS NULL AS is_open ORDER BY account_sortkey(account)"

expenses:
	2>/dev/null PYTHONPATH=$(BEANQUERY_PYTHONPATH) $(BEANQUERY) --format csv ledger/main.bean \
		"SELECT account, sum(position) as balance WHERE account ~ 'Expenses:' GROUP BY account ORDER BY account"

pre-commit:
	pre-commit run --all-files
