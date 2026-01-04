"""Beancount entry formatting utilities.

This module provides consistent formatting for Beancount entries across all parsers.
Uses Beancount's native printer for consistent formatting that matches bean-format.
"""

from __future__ import annotations

import beancount.core.data
from beancount.parser import printer


def format_entries(entries: list[beancount.core.data.Directive]) -> str:
    """Format a list of Beancount directives using the native Beancount printer.
    
    Args:
        entries: List of Beancount directives (Transaction, Balance, etc.).
        
    Returns:
        Formatted Beancount text with proper alignment and spacing.
    """
    if not entries:
        return ""
    
    lines: list[str] = []
    previous_was_balance = False
    
    for entry in entries:
        is_balance = isinstance(entry, beancount.core.data.Balance)
        is_transaction = isinstance(entry, beancount.core.data.Transaction)
        
        # Add blank line between entries, but not between consecutive balance directives
        if lines and (is_transaction or not previous_was_balance):
            lines.append("")
        
        # Use Beancount's native formatter
        formatted = printer.format_entry(entry)
        lines.append(formatted)
        
        previous_was_balance = is_balance
    
    return "\n".join(lines) + ("\n" if lines else "")

