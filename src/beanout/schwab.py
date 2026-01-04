"""Schwab bank JSON statement parsing and rendering.

This module re-exports the Schwab parser for backward compatibility.
The actual implementation is in beanout.entities.schwab.parser.
"""

# Re-export all public API from the new location
from beanout.entities.schwab.parser import (
    SchwabConfig,
    parse_schwab_json_text,
    parse_schwab_xml_text,
    render_schwab_json_file,
    render_schwab_json_file_to_jsonl,
    render_schwab_json_text,
    render_schwab_json_text_to_jsonl,
    render_schwab_xml_file,
    render_schwab_xml_file_to_jsonl,
    render_schwab_xml_text,
    render_schwab_xml_text_to_jsonl,
)

__all__ = [
    "SchwabConfig",
    "parse_schwab_json_text",
    "parse_schwab_xml_text",
    "render_schwab_json_file",
    "render_schwab_json_file_to_jsonl",
    "render_schwab_json_text",
    "render_schwab_json_text_to_jsonl",
    "render_schwab_xml_file",
    "render_schwab_xml_file_to_jsonl",
    "render_schwab_xml_text",
    "render_schwab_xml_text_to_jsonl",
]
