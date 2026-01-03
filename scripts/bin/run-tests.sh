#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

exec "$PYTHON_BIN" -m pytest \
  "${REPO_ROOT}/scripts/amortization/tests" \
  "${REPO_ROOT}/scripts/depreciation/tests"
