"""SPS Mortgage Servicing statement parser - main module.

This module provides the public API for parsing SPS Mortgage Servicing statements.
Supports PDF text format (.pdf.txt files).
"""

from typing import Optional

from beanout.common import io
from beanout.entities.sps.config import SPSConfig
from beanout.entities.sps import pdf_parser

# Re-export config for convenience
__all__ = [
    "SPSConfig",
    "parse_sps_text",
    "render_sps_text",
    "render_sps_file",
    "render_sps_text_to_jsonl",
    "render_sps_file_to_jsonl",
]


def parse_sps_text(text: str, config: Optional[SPSConfig] = None):
    """Parse SPS statement text into Beancount directives."""
    return pdf_parser.parse_pdf_text(text, config)


def render_sps_text(text: str, config: Optional[SPSConfig] = None) -> str:
    """Render SPS statement text into Beancount entries."""
    return pdf_parser.render_pdf_text(text, config)


def render_sps_file(filepath: str, config: Optional[SPSConfig] = None) -> str:
    """Render a *.pdf.txt SPS file into Beancount text."""
    return io.render_file_generic(
        filepath, ".pdf.txt", lambda text: render_sps_text(text, config)
    )


def render_sps_text_to_jsonl(text: str, config: Optional[SPSConfig] = None) -> str:
    """Render SPS statement text into JSONL format."""
    return pdf_parser.render_pdf_text_to_jsonl(text, config)


def render_sps_file_to_jsonl(filepath: str, config: Optional[SPSConfig] = None) -> str:
    """Render a *.pdf.txt SPS file into JSONL format."""
    return io.render_file_generic(
        filepath, ".pdf.txt", lambda text: render_sps_text_to_jsonl(text, config)
    )
