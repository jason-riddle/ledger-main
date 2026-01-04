"""Rendering utilities for converting Beancount directives to output formats.

This module provides utilities for rendering Beancount directives to
Beancount text format and JSONL format.
"""

import beancount.core.data

import beanout.formatter
import beanout.jsonl


def render_to_beancount(entries: list[beancount.core.data.Directive]) -> str:
    """Render Beancount directives to formatted Beancount text.

    Args:
        entries: List of Beancount directives.

    Returns:
        Formatted Beancount text.
    """
    return beanout.formatter.format_entries(entries)


def render_to_jsonl(entries: list[beancount.core.data.Directive]) -> str:
    """Render Beancount directives to JSONL format.

    Args:
        entries: List of Beancount directives.

    Returns:
        JSONL-formatted text.
    """
    return beanout.jsonl.directives_to_jsonl(entries)
