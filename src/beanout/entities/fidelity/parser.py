"""Fidelity brokerage statement parser - main module.

This module provides the public API for parsing Fidelity brokerage statements.
Supports CSV format.
"""

from typing import Optional

from beanout.common import io
from beanout.entities.fidelity.config import FidelityConfig
from beanout.entities.fidelity import csv_parser

# Re-export config for convenience
__all__ = [
    "FidelityConfig",
    "render_fidelity_csv_text",
    "render_fidelity_csv_file",
    "render_fidelity_csv_text_to_jsonl",
    "render_fidelity_csv_file_to_jsonl",
    "parse_fidelity_csv_text",
]


# CSV format functions
def parse_fidelity_csv_text(text: str, config: Optional[FidelityConfig] = None):
    """Parse Fidelity CSV content into Beancount directives."""
    return csv_parser.parse_csv_text(text, config)


def render_fidelity_csv_text(text: str, config: Optional[FidelityConfig] = None) -> str:
    """Render Fidelity CSV content into Beancount entries."""
    return csv_parser.render_csv_text(text, config)


def render_fidelity_csv_file(filepath: str, config: Optional[FidelityConfig] = None) -> str:
    """Render a *.csv Fidelity file into Beancount text."""
    # Note: Fidelity CSVs may have UTF-8 BOM, handled by csv_parser
    text = io.read_text_file(filepath, encoding="utf-8-sig")
    return render_fidelity_csv_text(text, config)


def render_fidelity_csv_text_to_jsonl(
    text: str, config: Optional[FidelityConfig] = None
) -> str:
    """Render Fidelity CSV content into JSONL format."""
    return csv_parser.render_csv_text_to_jsonl(text, config)


def render_fidelity_csv_file_to_jsonl(
    filepath: str, config: Optional[FidelityConfig] = None
) -> str:
    """Render a *.csv Fidelity file into JSONL format."""
    text = io.read_text_file(filepath, encoding="utf-8-sig")
    return render_fidelity_csv_text_to_jsonl(text, config)
