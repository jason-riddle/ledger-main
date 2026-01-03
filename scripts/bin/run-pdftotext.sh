#!/usr/bin/env bash
set -euo pipefail

if ! command -v pdftotext > /dev/null 2>&1; then
  echo "pdftotext not found in PATH" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

for root in documents fixtures; do
  target="${REPO_ROOT}/${root}"
  if [[ -d "${target}" ]]; then
    find "${target}" -type f -iname "*.pdf" -print0 | while IFS= read -r -d '' pdf; do
      pdftotext -layout "${pdf}" "${pdf}.txt"
      perl -0777 -pi -e 's/\s+\z/\n/s' "${pdf}.txt"
    done
  fi
done
