#!/usr/bin/env bash
set -euo pipefail

if ! command -v pdftotext > /dev/null 2>&1; then
  echo "pdftotext not found in PATH" >&2
  exit 1
fi

for root in documents fixtures; do
  if [[ -d "${root}" ]]; then
    find "${root}" -type f -iname "*.pdf" -print0 | while IFS= read -r -d '' pdf; do
      pdftotext -layout "${pdf}" "${pdf}.txt"
      perl -0777 -pi -e 's/\s+\z/\n/s' "${pdf}.txt"
    done
  fi
done
