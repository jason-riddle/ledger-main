UV_PYTHON_INSTALL_DIR ?= $(HOME)/.cache/uv/python

.PHONY: uv-sync test plugins-test

uv-sync:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv sync --dev

test:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv run pytest -q

plugins-test:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv run plugins/tests/test_find_duplicates.py -q
