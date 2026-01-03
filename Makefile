UV_PYTHON_INSTALL_DIR ?= $(HOME)/.cache/uv/python
BEANCHECK_BIN ?= bean-check
BEANQUERY_BIN ?= bean-query

.PHONY: uv-sync test plugins-test check

uv-sync:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv sync --dev

test:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv run pytest -q

plugins-test:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv run plugins/tests/test_find_duplicates.py -q

check:
	PYTHONPATH=$(CURDIR) $(BEANCHECK_BIN) ledger/main.bean

query:
	PYTHONPATH=$(CURDIR) $(BEANQUERY_BIN) ledger/main.bean
