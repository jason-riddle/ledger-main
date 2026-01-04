"""Ally Bank statement parsing and rendering.

This module re-exports the Ally Bank parser for backward compatibility.
The actual implementation is in beanout.entities.ally_bank.parser.
"""

# Re-export all public API from the new location
from beanout.entities.ally_bank.parser import (
    AllyBankConfig,
    parse_ally_bank_csv_text,
    parse_ally_bank_qfx_text,
    render_ally_bank_csv_file,
    render_ally_bank_csv_file_to_jsonl,
    render_ally_bank_csv_text,
    render_ally_bank_csv_text_to_jsonl,
    render_ally_bank_qfx_file,
    render_ally_bank_qfx_file_to_jsonl,
    render_ally_bank_qfx_text,
    render_ally_bank_qfx_text_to_jsonl,
)

__all__ = [
    "AllyBankConfig",
    "parse_ally_bank_csv_text",
    "parse_ally_bank_qfx_text",
    "render_ally_bank_csv_file",
    "render_ally_bank_csv_file_to_jsonl",
    "render_ally_bank_csv_text",
    "render_ally_bank_csv_text_to_jsonl",
    "render_ally_bank_qfx_file",
    "render_ally_bank_qfx_file_to_jsonl",
    "render_ally_bank_qfx_text",
    "render_ally_bank_qfx_text_to_jsonl",
]
