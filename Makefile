UV_PYTHON_INSTALL_DIR ?= $(HOME)/.cache/uv/python
UV_RUN ?= UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv run
BEANQUERY_HOME ?= $(TMPDIR)/beanquery-home

.PHONY: uv-sync test plugins-test check pre-commit

uv-sync:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv sync --dev

test:
	$(UV_RUN) pytest -q

plugins-test:
	$(UV_RUN) plugins/tests/test_find_duplicates.py -q

check:
	PYTHONPATH=$(CURDIR) $(UV_RUN) bean-check ledger/main.bean

query:
	mkdir -p $(BEANQUERY_HOME)/.config/beanquery
	HOME=$(BEANQUERY_HOME) PYTHONPATH=$(CURDIR) $(UV_RUN) bean-query ledger/main.bean

pre-commit:
	PYTHONPATH=$(CURDIR) pre-commit run --all-files
