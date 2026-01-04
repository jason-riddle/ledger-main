"""Fidelity brokerage CSV parsing and rendering.

This module re-exports the Fidelity parser for backward compatibility.
The actual implementation is in beanout.entities.fidelity.parser.
"""

# Re-export all public API from the new location
from beanout.entities.fidelity.parser import (
    FidelityConfig,
    parse_fidelity_csv_text,
    render_fidelity_csv_file,
    render_fidelity_csv_file_to_jsonl,
    render_fidelity_csv_text,
    render_fidelity_csv_text_to_jsonl,
)

__all__ = [
    "FidelityConfig",
    "parse_fidelity_csv_text",
    "render_fidelity_csv_file",
    "render_fidelity_csv_file_to_jsonl",
    "render_fidelity_csv_text",
    "render_fidelity_csv_text_to_jsonl",
]
