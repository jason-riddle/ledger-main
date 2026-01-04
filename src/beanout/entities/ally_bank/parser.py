"""Ally Bank statement parser - main module.

This module provides the public API for parsing Ally Bank statements.
Supports both CSV and QFX formats.
"""

from typing import Optional

from beanout.common import io
from beanout.entities.ally_bank.config import AllyBankConfig
from beanout.entities.ally_bank import csv_parser, qfx_parser

# Re-export config for convenience
__all__ = [
    "AllyBankConfig",
    "render_ally_bank_csv_text",
    "render_ally_bank_csv_file",
    "render_ally_bank_csv_text_to_jsonl",
    "render_ally_bank_csv_file_to_jsonl",
    "parse_ally_bank_csv_text",
    "render_ally_bank_qfx_text",
    "render_ally_bank_qfx_file",
    "render_ally_bank_qfx_text_to_jsonl",
    "render_ally_bank_qfx_file_to_jsonl",
    "parse_ally_bank_qfx_text",
]


# CSV format functions
def parse_ally_bank_csv_text(text: str, config: Optional[AllyBankConfig] = None):
    """Parse Ally Bank CSV content into Beancount directives."""
    return csv_parser.parse_csv_text(text, config)


def render_ally_bank_csv_text(text: str, config: Optional[AllyBankConfig] = None) -> str:
    """Render Ally Bank CSV content into Beancount entries."""
    return csv_parser.render_csv_text(text, config)


def render_ally_bank_csv_file(filepath: str, config: Optional[AllyBankConfig] = None) -> str:
    """Render a *.csv Ally Bank file into Beancount text."""
    return io.render_file_generic(
        filepath, ".csv", lambda text: render_ally_bank_csv_text(text, config)
    )


def render_ally_bank_csv_text_to_jsonl(
    text: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render Ally Bank CSV content into JSONL format."""
    return csv_parser.render_csv_text_to_jsonl(text, config)


def render_ally_bank_csv_file_to_jsonl(
    filepath: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render a *.csv Ally Bank file into JSONL format."""
    return io.render_file_generic(
        filepath, ".csv", lambda text: render_ally_bank_csv_text_to_jsonl(text, config)
    )


# QFX format functions
def parse_ally_bank_qfx_text(
    text: str | bytes, config: Optional[AllyBankConfig] = None
):
    """Parse Ally Bank QFX content into Beancount directives."""
    return qfx_parser.parse_qfx_data(text, config)


def render_ally_bank_qfx_text(
    text: str | bytes, config: Optional[AllyBankConfig] = None
) -> str:
    """Render Ally Bank QFX content into Beancount entries."""
    return qfx_parser.render_qfx_data(text, config)


def render_ally_bank_qfx_file(filepath: str, config: Optional[AllyBankConfig] = None) -> str:
    """Render a *.qfx Ally Bank file into Beancount text."""
    return io.render_binary_file_generic(
        filepath, ".qfx", lambda data: render_ally_bank_qfx_text(data, config)
    )


def render_ally_bank_qfx_text_to_jsonl(
    text: str | bytes, config: Optional[AllyBankConfig] = None
) -> str:
    """Render Ally Bank QFX content into JSONL format."""
    return qfx_parser.render_qfx_data_to_jsonl(text, config)


def render_ally_bank_qfx_file_to_jsonl(
    filepath: str, config: Optional[AllyBankConfig] = None
) -> str:
    """Render a *.qfx Ally Bank file into JSONL format."""
    return io.render_binary_file_generic(
        filepath, ".qfx", lambda data: render_ally_bank_qfx_text_to_jsonl(data, config)
    )
