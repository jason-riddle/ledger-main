# export UV_PYTHON_INSTALL_DIR ?= $(HOME)/.cache/uv/python

.PHONY: uv-sync test plugins-test check query query-cmd pre-commit

uv-sync:
	uv sync --dev

test:
	uv run pytest -q

plugins-test:
	uv run plugins/tests/test_find_duplicates.py -q

check:
	PYTHONPATH=$(CURDIR) uv run bean-check ledger/main.bean

query:
	PYTHONPATH=$(CURDIR) uv run python scripts/bin/bean-query-nohistory.py ledger/main.bean

query-cmd:
	@if [ -z "$(QUERY)" ]; then echo "Usage: make query-cmd QUERY='select ...'"; exit 2; fi
	PYTHONPATH=$(CURDIR) uv run python scripts/bin/bean-query-nohistory.py ledger/main.bean "$(QUERY)"

pre-commit:
	PYTHONPATH=$(CURDIR) pre-commit run --all-files
