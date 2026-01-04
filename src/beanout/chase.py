"""Chase credit card statement parsing and rendering.

This module re-exports the Chase parser for backward compatibility.
The actual implementation is in beanout.entities.chase.parser.
"""

# Re-export all public API from the new location
from beanout.entities.chase.parser import (
    ChaseConfig,
    parse_chase_csv_text,
    parse_chase_qfx_text,
    render_chase_csv_file,
    render_chase_csv_file_to_jsonl,
    render_chase_csv_text,
    render_chase_csv_text_to_jsonl,
    render_chase_qfx_file,
    render_chase_qfx_file_to_jsonl,
    render_chase_qfx_text,
    render_chase_qfx_text_to_jsonl,
)

__all__ = [
    "ChaseConfig",
    "parse_chase_csv_text",
    "parse_chase_qfx_text",
    "render_chase_csv_file",
    "render_chase_csv_file_to_jsonl",
    "render_chase_csv_text",
    "render_chase_csv_text_to_jsonl",
    "render_chase_qfx_file",
    "render_chase_qfx_file_to_jsonl",
    "render_chase_qfx_text",
    "render_chase_qfx_text_to_jsonl",
]
