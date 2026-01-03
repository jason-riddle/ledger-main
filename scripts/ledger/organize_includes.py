#!/usr/bin/env -S uv run

# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Organize include-only Beancount files.

Sorts section headers and the lines within each section lexicographically.
"""

from __future__ import annotations

import argparse
import pathlib
import sys


def is_section_header(line: str) -> bool:
    """Return True if a line is a section header."""
    return line.startswith("; ") and not line.startswith(";;")


def organize_text(text: str) -> str:
    """Return organized text with sorted sections and lines."""
    lines = text.splitlines()
    section_indices = [idx for idx, line in enumerate(lines) if is_section_header(line)]
    if not section_indices:
        return text if text.endswith("\n") else text + "\n"

    preamble = lines[: section_indices[0]]
    sections: list[tuple[str, list[str]]] = []

    for i, start in enumerate(section_indices):
        end = section_indices[i + 1] if i + 1 < len(section_indices) else len(lines)
        header = lines[start]
        body = [line for line in lines[start + 1 : end] if line.strip()]
        sections.append((header, sorted(body)))

    sections.sort(key=lambda item: item[0][2:].strip())

    output_lines: list[str] = []
    output_lines.extend(preamble)
    for header, body in sections:
        output_lines.append(header)
        output_lines.extend(body)
        output_lines.append("")

    while output_lines and output_lines[-1] == "":
        output_lines.pop()

    return "\n".join(output_lines) + "\n"


def load_organize_list(
    path: pathlib.Path, repo_root: pathlib.Path
) -> list[pathlib.Path]:
    """Load paths from a manifest file, supporting simple globs."""
    paths: list[pathlib.Path] = []
    content = path.read_text(encoding="utf-8").splitlines()
    for raw_line in content:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if any(char in line for char in "*?["):
            paths.extend(sorted(repo_root.glob(line)))
        else:
            paths.append(repo_root / line)
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Organize include-only .bean files.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or globs to organize (relative to repo root if not absolute).",
    )
    parser.add_argument(
        "--organize-file",
        dest="organize_file",
        help="Path to a manifest listing files/globs to organize.",
    )
    parser.add_argument("--check", action="store_true", help="Fail if changes needed.")
    parser.add_argument("--write", action="store_true", help="Rewrite files in place.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check == args.write:
        print("Error: choose exactly one of --check or --write.", file=sys.stderr)
        return 2

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    file_paths: list[pathlib.Path] = []

    if args.organize_file:
        manifest_path = pathlib.Path(args.organize_file)
        if not manifest_path.is_absolute():
            manifest_path = repo_root / manifest_path
        if not manifest_path.exists():
            print(f"Error: organize file not found: {manifest_path}", file=sys.stderr)
            return 2
        file_paths.extend(load_organize_list(manifest_path, repo_root))

    for raw_path in args.paths:
        path = pathlib.Path(raw_path)
        if not path.is_absolute():
            path = repo_root / path
        if any(char in raw_path for char in "*?["):
            file_paths.extend(sorted(repo_root.glob(raw_path)))
        else:
            file_paths.append(path)

    unique_paths = []
    seen = set()
    for path in file_paths:
        resolved = path.resolve()
        if resolved not in seen:
            unique_paths.append(path)
            seen.add(resolved)

    if not unique_paths:
        print("Error: no files provided to organize.", file=sys.stderr)
        return 2

    changed = []
    for path in unique_paths:
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            return 2
        original = path.read_text(encoding="utf-8")
        organized = organize_text(original)
        if organized != original:
            changed.append(path)
            if args.write:
                path.write_text(organized, encoding="utf-8")

    if args.check and changed:
        print("Files need organizing:", file=sys.stderr)
        for path in changed:
            print(f"- {path}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
