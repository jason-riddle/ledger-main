"""SPS Mortgage Servicing statement parsing and rendering.

This module re-exports the SPS parser for backward compatibility.
The actual implementation is in beanout.entities.sps.parser.
"""

# Re-export all public API from the new location
from beanout.entities.sps.parser import (
    SPSConfig,
    parse_sps_text,
    render_sps_file,
    render_sps_file_to_jsonl,
    render_sps_text,
    render_sps_text_to_jsonl,
)

__all__ = [
    "SPSConfig",
    "parse_sps_text",
    "render_sps_file",
    "render_sps_file_to_jsonl",
    "render_sps_text",
    "render_sps_text_to_jsonl",
]
