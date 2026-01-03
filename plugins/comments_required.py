"""Require comments metadata on transactions."""

import collections

from beancount.core import data

__plugins__ = ["validate_comments"]

CommentsError = collections.namedtuple("CommentsError", "source message entry")


def validate_comments(entries, options_map):
    """Validate that transactions include comments metadata."""
    del options_map  # Unused.
    errors = []
    for entry in entries:
        if isinstance(entry, data.Transaction):
            if not entry.meta or "comments" not in entry.meta:
                source = (
                    entry.meta
                    if entry.meta
                    else data.new_metadata("<comments_required>", 0)
                )
                errors.append(
                    CommentsError(
                        source,
                        "Missing 'comments' metadata on transaction",
                        entry,
                    )
                )
    return entries, errors
