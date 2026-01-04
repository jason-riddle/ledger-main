"""OFX (Open Financial Exchange) parsing utilities.

This module provides shared utilities for parsing OFX/QFX files
commonly used by banks and credit card companies.
"""

import io
from typing import Any

from ofxtools.Parser import OFXTree


def parse_ofx_data(data: str | bytes) -> Any:
    """Parse OFX data into an OFX object.

    Args:
        data: OFX data as string or bytes.

    Returns:
        Parsed OFX object.
    """
    if isinstance(data, bytes):
        payload = data
    else:
        payload = data.encode("utf-8")

    parser = OFXTree()
    parser.parse(io.BytesIO(payload))

    # Clean up severity values
    for severity in parser.findall(".//SEVERITY"):
        if severity.text:
            severity.text = severity.text.strip().upper()

    return parser.convert()


def build_ofx_narration(tx_type: str, name: str, memo: str, fallback: str = "Activity") -> str:
    """Build a narration string from OFX transaction fields.

    Args:
        tx_type: Transaction type.
        name: Transaction name.
        memo: Transaction memo.
        fallback: Fallback text if all fields are empty.

    Returns:
        Formatted narration string.
    """
    parts = [value for value in (tx_type, name, memo) if value]
    if not parts:
        return fallback
    return " - ".join(parts)
