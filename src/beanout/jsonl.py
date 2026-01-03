"""Convert Beancount directives to JSONL format."""

import json
from typing import Any

import beancount.core.data


def transaction_to_jsonl_object(txn: beancount.core.data.Transaction) -> dict[str, Any]:
    """Convert a Beancount Transaction to a JSONL object.

    Args:
        txn: Beancount Transaction directive.

    Returns:
        Dictionary matching the transaction schema.
    """
    # Extract property from tags (e.g., "206-hoover-ave" -> "206-Hoover-Ave")
    property_value = _extract_property_from_transaction(txn)

    # Build entries list
    entries = []
    for posting in txn.postings:
        entries.append(
            {
                "account": posting.account,
                "amount_usd": float(posting.units.number),
            }
        )

    # Build transaction object
    transaction_obj = {
        "date": txn.date.isoformat(),
        "property": property_value,
        "payee_payer": txn.payee or "",
        "description": txn.narration or "",
        "entries": entries,
    }

    # Add tags if present
    if txn.tags:
        transaction_obj["tags"] = sorted(txn.tags)

    return {
        "ok": True,
        "transaction": transaction_obj,
    }


def _extract_property_from_transaction(
    txn: beancount.core.data.Transaction,
) -> str:
    """Extract property identifier from transaction tags or accounts.

    Args:
        txn: Beancount Transaction directive.

    Returns:
        Property identifier (e.g., "206-Hoover-Ave", "2943-Butterfly-Palm", "Unassigned").
    """
    # Map of common tag patterns to property names
    property_map = {
        "206-hoover-ave": "206-Hoover-Ave",
        "2943-butterfly-palm": "2943-Butterfly-Palm",
    }

    # Check tags first
    for tag in txn.tags:
        tag_lower = tag.lower()
        if tag_lower in property_map:
            return property_map[tag_lower]

    # Check account names for property patterns
    for posting in txn.postings:
        account = posting.account
        for pattern, property_name in property_map.items():
            # Convert pattern to account-style (e.g., "206-hoover-ave" -> "206-Hoover-Ave")
            if property_name in account:
                return property_name

    return "Unassigned"


def directives_to_jsonl(
    directives: list[beancount.core.data.Directive],
) -> str:
    """Convert list of Beancount directives to JSONL format.

    Only Transaction directives are converted. Other directives (Balance, etc.) are skipped.

    Args:
        directives: List of Beancount directives.

    Returns:
        JSONL-formatted string (one JSON object per line).
    """
    lines = []
    for directive in directives:
        if isinstance(directive, beancount.core.data.Transaction):
            obj = transaction_to_jsonl_object(directive)
            lines.append(json.dumps(obj, ensure_ascii=False))

    return "\n".join(lines) + ("\n" if lines else "")
