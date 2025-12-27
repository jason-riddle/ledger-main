from collections import namedtuple

from beancount.core import data

__plugins__ = ["validate_comments"]

CommentsError = namedtuple("CommentsError", "source message entry")


def validate_comments(entries, options_map):
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
