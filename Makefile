UV_PYTHON_INSTALL_DIR ?= $(HOME)/.cache/uv/python

.PHONY: uv-sync test

uv-sync:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv sync --dev

test:
	UV_PYTHON_INSTALL_DIR=$(UV_PYTHON_INSTALL_DIR) uv run pytest -q
