"""Schwab bank statement parser - main module.

This module provides the public API for parsing Schwab bank statements.
Supports both JSON and XML formats.
"""

from typing import Optional

from beanout.common import io
from beanout.entities.schwab.config import SchwabConfig
from beanout.entities.schwab import json_parser, xml_parser

# Re-export config for convenience
__all__ = [
    "SchwabConfig",
    "render_schwab_json_text",
    "render_schwab_json_file",
    "render_schwab_json_text_to_jsonl",
    "render_schwab_json_file_to_jsonl",
    "parse_schwab_json_text",
    "render_schwab_xml_text",
    "render_schwab_xml_file",
    "render_schwab_xml_text_to_jsonl",
    "render_schwab_xml_file_to_jsonl",
    "parse_schwab_xml_text",
]


# JSON format functions
def parse_schwab_json_text(text: str, config: Optional[SchwabConfig] = None):
    """Parse Schwab JSON content into Beancount directives."""
    return json_parser.parse_json_text(text, config)


def render_schwab_json_text(text: str, config: Optional[SchwabConfig] = None) -> str:
    """Render Schwab JSON content into Beancount entries."""
    return json_parser.render_json_text(text, config)


def render_schwab_json_file(filepath: str, config: Optional[SchwabConfig] = None) -> str:
    """Render a *.json Schwab file into Beancount text."""
    return io.render_file_generic(
        filepath, ".json", lambda text: render_schwab_json_text(text, config)
    )


def render_schwab_json_text_to_jsonl(
    text: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab JSON content into JSONL format."""
    return json_parser.render_json_text_to_jsonl(text, config)


def render_schwab_json_file_to_jsonl(
    filepath: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render a *.json Schwab file into JSONL format."""
    return io.render_file_generic(
        filepath, ".json", lambda text: render_schwab_json_text_to_jsonl(text, config)
    )


# XML format functions
def parse_schwab_xml_text(
    text: str | bytes, config: Optional[SchwabConfig] = None
):
    """Parse Schwab XML content into Beancount directives."""
    return xml_parser.parse_xml_data(text, config)


def render_schwab_xml_text(
    text: str | bytes, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab XML content into Beancount entries."""
    return xml_parser.render_xml_data(text, config)


def render_schwab_xml_file(filepath: str, config: Optional[SchwabConfig] = None) -> str:
    """Render a *.xml Schwab file into Beancount text."""
    return io.render_binary_file_generic(
        filepath, ".xml", lambda data: render_schwab_xml_text(data, config)
    )


def render_schwab_xml_text_to_jsonl(
    text: str | bytes, config: Optional[SchwabConfig] = None
) -> str:
    """Render Schwab XML content into JSONL format."""
    return xml_parser.render_xml_data_to_jsonl(text, config)


def render_schwab_xml_file_to_jsonl(
    filepath: str, config: Optional[SchwabConfig] = None
) -> str:
    """Render a *.xml Schwab file into JSONL format."""
    return io.render_binary_file_generic(
        filepath, ".xml", lambda data: render_schwab_xml_text_to_jsonl(data, config)
    )
