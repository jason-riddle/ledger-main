#!/usr/bin/env python3
"""Generate ledger/years/YYYY.bean from ledger/canonical."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List

YEAR_RE = re.compile(r"^(\d{4})-")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _should_ignore(path: Path) -> bool:
    if "_notes" in path.parts:
        return True
    if path.name.startswith("draft-"):
        return True
    return False


def _collect_year_files(
    canonical_dir: Path, year_filter: str | None
) -> Dict[str, Dict[str, List[Path]]]:
    years: Dict[str, Dict[str, List[Path]]] = {}
    for file_path in canonical_dir.rglob("*.bean"):
        if _should_ignore(file_path):
            continue
        match = YEAR_RE.match(file_path.name)
        if not match:
            continue
        year = match.group(1)
        if year_filter and year != year_filter:
            continue
        rel = file_path.relative_to(canonical_dir)
        if not rel.parts:
            continue
        group = rel.parts[0]
        years.setdefault(year, {}).setdefault(group, []).append(rel)
    return years


def _render_year_file(year: str, groups: Dict[str, List[Path]]) -> str:
    lines: List[str] = []
    lines.append("; AUTO-GENERATED. DO NOT EDIT.\n")
    lines.append(";;\n")
    lines.append(f";; {year} - YEAR - ALL\n")
    lines.append(";;\n")

    for group in sorted(groups.keys()):
        lines.append("\n")
        lines.append(f"; {group.upper()}\n")
        for rel in sorted(groups[group], key=lambda p: p.as_posix()):
            include_path = f"../canonical/{rel.as_posix()}"
            lines.append(f'include "{include_path}"\n')

    return "".join(lines).lstrip("\n")


def _update_main(main_bean: Path, years: List[str], dry_run: bool) -> None:
    if not main_bean.exists():
        return

    lines = main_bean.read_text().splitlines(keepends=True)

    year_block_indexes = []
    for i, line in enumerate(lines):
        match = re.match(r"^;;\s+(\d{4})\s*$", line)
        if not match:
            continue
        include_idx = None
        for j in range(i + 1, min(i + 6, len(lines))):
            if lines[j].lstrip().startswith('include "'):
                include_idx = j
                break
        if include_idx is None:
            continue
        year_block_indexes.append((i, include_idx + 1))

    if not year_block_indexes:
        return

    start = min(idx[0] for idx in year_block_indexes)
    end = max(idx[1] for idx in year_block_indexes)
    while end < len(lines) and lines[end].strip() == "":
        end += 1

    new_block: List[str] = []
    for year in years:
        new_block.append(";;\n")
        new_block.append(f";; {year}\n")
        new_block.append(";;\n")
        new_block.append("\n")
        new_block.append(f'include "./years/{year}.bean"\n')
        new_block.append("\n")

    updated = lines[:start] + new_block + lines[end:]
    if dry_run:
        return
    main_bean.write_text("".join(updated))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate ledger/years/YYYY.bean from ledger/canonical."
    )
    parser.add_argument(
        "--year", help="Only generate the specified year (YYYY).", default=None
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print actions without writing files."
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    canonical_dir = repo_root / "ledger" / "canonical"
    years_dir = repo_root / "ledger" / "years"
    main_bean = repo_root / "ledger" / "main.bean"

    if not canonical_dir.exists():
        raise SystemExit(f"canonical dir not found: {canonical_dir}")

    years = _collect_year_files(canonical_dir, args.year)
    if not years:
        return 0

    years_dir.mkdir(parents=True, exist_ok=True)

    for year, groups in sorted(years.items()):
        content = _render_year_file(year, groups)
        year_file = years_dir / f"{year}.bean"
        if args.dry_run:
            print(f"== {year_file} ==")
            print(content)
            continue
        year_file.write_text(content)

    _update_main(main_bean, sorted(years.keys()), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
