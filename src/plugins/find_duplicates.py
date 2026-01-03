"""Detect duplicate transaction candidates with confidence scoring.

This plugin compares transactions within a small date window and emits
warnings or errors when a confidence threshold is met.
"""

import collections
import decimal
import logging
import re
import shlex

import beancount.core.data as data
import beancount.core.number as number

__plugins__ = ["plugin"]

# Weights for confidence score calculation in duplicate detection.
# These determine the relative importance of each matching factor:
# - amount: How closely the transaction amounts match (within tolerance)
# - date: How close the transaction dates are (within date window)
# - account: Whether the transactions share any cash accounts
_WEIGHTS = {
    "amount": 0.5,
    "date": 0.3,
    "account": 0.2,
}

# Default matching thresholds and behavior:
# - error_score_threshold: minimum confidence score (0.0-1.0) required to emit an error for a potential duplicate pair.
#   Transactions with confidence scores above this threshold are considered definite duplicates and will cause
#   the plugin to fail validation.
# - warn_score_threshold: minimum confidence score (0.0-1.0) required to emit a warning for a potential duplicate pair.
#   Transactions with confidence scores above this threshold but below error_score_threshold will generate
#   warning messages but allow validation to pass.
# - date_window_days: maximum number of days between transactions that will be considered as potential duplicates.
#   This window is used both for generating candidate pairs and for calculating the date similarity score,
#   which decays linearly from 1.0 (same date) to 0.0 (date_window_days apart).
# - amount_tolerance: maximum allowed absolute difference in net transaction amounts for them to be considered
#   a perfect amount match. For example, with a tolerance of $0.03, transactions with amounts $100.00 and $100.02
#   would receive a full amount score of 1.0, while $100.00 and $100.04 would receive 0.0.
# - cash_accounts_only: when true, limit amount/currency matching to Assets:* postings so the
#   detector keys off the cash-side postings (typically the most stable signal) even when non-cash
#   categorization differs between sources or imports.
#   (e.g., a txn with only Income/Expense postings is excluded when true; included when false).
# - require_property_match: when true, require matching property tokens (regex ^[0-9]{3,4}-[A-Za-z].*)
#   gathered from tags like #206-hoover-ave or account segments like Assets:...:2943-Butterfly-Palm:...
#   (e.g., #206-hoover-ave vs #2943-butterfly-palm blocks a match when true; allowed when false).
_DEFAULT_CONFIG = {
    "error_score_threshold": 0.95,
    "warn_score_threshold": 0.80,
    "date_window_days": 3,
    "amount_tolerance": decimal.Decimal("0.03"),
    "cash_accounts_only": False,
    "require_property_match": False,
}

DuplicateError = collections.namedtuple("DuplicateError", "source message entry")


def plugin(entries, unused_options_map, config_str=""):
    """Validate duplicate candidates.

    Args:
        entries: Beancount entries.
        unused_options_map: Unused.
        config_str: Optional configuration string.

    Returns:
        A tuple of (entries, diagnostics).
    """
    del unused_options_map  # Unused by design; plugin signature requires it.
    cfg = parse_config(config_str)
    txns = [entry for entry in entries if isinstance(entry, data.Transaction)]
    diagnostics = []

    index = index_transactions(txns, cfg)

    for group in index.values():
        for txn_a, txn_b in candidate_pairs(group, cfg["date_window_days"]):
            score, parts = confidence_score(txn_a, txn_b, cfg)
            if score >= cfg["error_score_threshold"]:
                diagnostics.append(_error(txn_b, txn_a, score, parts))
            elif score >= cfg["warn_score_threshold"]:
                _warn(txn_b, txn_a, score, parts)

    return entries, diagnostics


def parse_config(config_str):
    """Parse the plugin configuration string into a dict."""
    cfg = dict(_DEFAULT_CONFIG)
    aliases = {
        "warn_threshold": "warn_score_threshold",
        "error_threshold": "error_score_threshold",
        "window": "date_window_days",
        "tolerance": "amount_tolerance",
        "cash_only": "cash_accounts_only",
        "property_match": "require_property_match",
    }
    for part in shlex.split(config_str):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = aliases.get(key, key)
        if key == "date_window_days":
            cfg[key] = int(value)
        elif key == "amount_tolerance":
            cfg[key] = decimal.Decimal(value)
        elif key == "cash_accounts_only":
            cfg[key] = value.lower() in {"1", "true", "yes"}
        elif key == "require_property_match":
            cfg[key] = value.lower() in {"1", "true", "yes"}
        else:
            cfg[key] = float(value)
    return cfg


def index_transactions(txns, cfg):
    """Index transactions by currency and amount when tolerance is zero."""
    index = collections.defaultdict(list)
    for txn in txns:
        currency = _first_currency(txn, cfg["cash_accounts_only"])
        if currency is None:
            continue
        amount = abs(net_amount(txn, cfg["cash_accounts_only"]))
        if amount is None:
            continue
        if cfg["amount_tolerance"] == number.ZERO:
            key = (currency, amount)
        else:
            key = (currency,)
        index[key].append(txn)
    return index


def candidate_pairs(txns, window):
    """Yield pairs of transactions within the date window."""
    txns = sorted(txns, key=lambda txn: txn.date)
    for i, txn_a in enumerate(txns):
        for txn_b in txns[i + 1 :]:
            if abs((txn_b.date - txn_a.date).days) > window:
                break
            yield txn_a, txn_b


def confidence_score(txn_a, txn_b, cfg):
    """Compute confidence score and component details."""
    property_val = None
    if cfg["require_property_match"]:
        property_val = property_score(txn_a, txn_b)
        if property_val == 0.0 and _has_property_tokens(txn_a, txn_b):
            parts = {
                "amount": 0.0,
                "date": 0.0,
                "account": 0.0,
                "property": 0.0,
            }
            return 0.0, parts

    amount_val = amount_score(
        txn_a,
        txn_b,
        cfg["amount_tolerance"],
        cfg["cash_accounts_only"],
    )
    date_val = date_score(txn_a, txn_b, cfg["date_window_days"])
    account_val = account_score(txn_a, txn_b)

    weights = dict(_WEIGHTS)
    if cfg["require_property_match"]:
        weights["property"] = 0.2
    total_weight = sum(weights.values())
    score = (
        weights["amount"] * amount_val
        + weights["date"] * date_val
        + weights["account"] * account_val
    )
    if cfg["require_property_match"]:
        score += weights["property"] * (property_val or 0.0)
    if total_weight:
        score /= total_weight

    parts = {
        "amount": amount_val,
        "date": date_val,
        "account": account_val,
    }
    if cfg["require_property_match"]:
        parts["property"] = property_val or 0.0
    return min(1.0, score), parts


def amount_score(txn_a, txn_b, tolerance, cash_only):
    """Return 1.0 if net amounts match within tolerance."""
    amount_a = net_amount(txn_a, cash_only)
    amount_b = net_amount(txn_b, cash_only)
    if amount_a is None or amount_b is None:
        return 0.0
    assert amount_a is not None and amount_b is not None
    delta = abs(amount_a - amount_b)
    return 1.0 if delta <= tolerance else 0.0


def date_score(txn_a, txn_b, window):
    """Return linear decay score within the window."""
    if window <= 0:
        return 0.0
    delta = abs((txn_a.date - txn_b.date).days)
    return max(0.0, 1.0 - (delta / window))


def account_score(txn_a, txn_b):
    """Return 1.0 if any cash account matches, else 0.0."""
    return 1.0 if cash_accounts(txn_a) & cash_accounts(txn_b) else 0.0


def net_amount(txn, cash_only):
    """Return the net numeric amount of postings in a transaction."""
    postings = _postings_for_amount(txn, cash_only)
    if not postings:
        return None
    total = number.ZERO
    for posting in postings:
        total += posting.units.number
    return total


def cash_accounts(txn):
    """Return a set of cash-like account names for a transaction."""
    return {
        posting.account
        for posting in txn.postings
        if posting.account.startswith("Assets:")
    }


def property_score(txn_a, txn_b):
    """Return 1.0 when property tokens overlap, else 0.0."""
    tokens_a = property_tokens(txn_a)
    tokens_b = property_tokens(txn_b)
    if not tokens_a or not tokens_b:
        return 0.0
    return 1.0 if tokens_a & tokens_b else 0.0


def message(txn_a, txn_b, score, parts):
    """Build a diagnostic message for a duplicate candidate."""
    detail = ", ".join(f"{key}={value:.2f}" for key, value in parts.items())
    return (
        f"Duplicate confidence {score:.2f} ({detail}): "
        f"{txn_b.date} likely duplicates {txn_a.date}"
    )


def _error(txn_b, txn_a, score, parts):
    """Build a diagnostic error entry."""
    source = txn_b.meta or data.new_metadata("<find_duplicates>", 0)
    return DuplicateError(source, message(txn_a, txn_b, score, parts), txn_b)


def _warn(txn_b, txn_a, score, parts):
    """Log a diagnostic warning."""
    logging.warning(message(txn_a, txn_b, score, parts))


def _first_currency(txn, cash_only):
    """Return the first currency found in postings."""
    postings = _postings_for_amount(txn, cash_only)
    if not postings:
        return None
    for posting in postings:
        return posting.units.currency
    return None


def _postings_for_amount(txn, cash_only):
    """Return postings considered for amount comparisons."""
    postings = []
    for posting in txn.postings:
        if posting.units is None:
            continue
        if cash_only and not posting.account.startswith("Assets:"):
            continue
        postings.append(posting)
    return postings


def property_tokens(txn):
    """Extract property tags or account tokens from a transaction."""
    tokens = set()
    for tag in txn.tags or set():
        if _PROPERTY_RE.match(tag):
            tokens.add(tag.lower())
    for posting in txn.postings:
        for segment in posting.account.split(":"):
            if _PROPERTY_RE.match(segment):
                tokens.add(segment.lower())
    return tokens


def _has_property_tokens(txn_a, txn_b):
    """Return True when both transactions include property tokens."""
    return bool(property_tokens(txn_a)) and bool(property_tokens(txn_b))


_PROPERTY_RE = re.compile(r"^[0-9]{3,4}-[A-Za-z].*")
