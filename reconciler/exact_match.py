"""
Exact matching stage of the reconciliation pipeline.

Strategy
--------
Group both sets of transactions by reference_number.
A pair is an exact match when one gateway record and one bank record share
the same reference_number.  All remaining records become inputs to the fuzzy
matching stage.

Public API
----------
exact_match(gateway, bank) -> ExactMatchResult
"""

from __future__ import annotations

import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass, field

from .models import MatchResult, MatchStatus, Transaction

logger = logging.getLogger(__name__)


@dataclass
class ExactMatchResult:
    """Output of the exact matching stage."""

    matched: list[MatchResult] = field(default_factory=list)
    unmatched_gateway: list[Transaction] = field(default_factory=list)
    unmatched_bank: list[Transaction] = field(default_factory=list)


def exact_match(
    gateway: list[Transaction],
    bank: list[Transaction],
) -> ExactMatchResult:
    """
    Match gateway transactions against bank transactions on reference_number.

    Handles duplicates within each file gracefully: if multiple records share
    the same reference_number in the same file, only the first is matched and
    the rest are left unmatched for the fuzzy stage (they will ultimately
    surface as exceptions).

    Parameters
    ----------
    gateway : parsed gateway transactions
    bank    : parsed bank transactions

    Returns
    -------
    ExactMatchResult with matched pairs and leftover unmatched lists
    """
    gw_by_ref: dict[str, list[Transaction]] = _group_by_ref(gateway)
    bank_by_ref: dict[str, list[Transaction]] = _group_by_ref(bank)

    result = ExactMatchResult()
    matched_refs: set[str] = set()

    for ref, gw_list in gw_by_ref.items():
        if ref in bank_by_ref:
            bank_list = bank_by_ref[ref]

            # Consume the first pair as the match
            gw_tx = gw_list[0]
            bank_tx = bank_list[0]

            notes = _discrepancy_notes(gw_tx, bank_tx)
            result.matched.append(
                MatchResult(
                    gateway_tx=gw_tx,
                    bank_tx=bank_tx,
                    status=MatchStatus.EXACT,
                    confidence=1.0,
                    rule_score=1.0,
                    discrepancy_notes=notes,
                    llm_reasoning="Exact reference_number match.",
                    matched_at=datetime.datetime.now(),
                )
            )
            matched_refs.add(ref)

            # Any extras beyond the first pair go to the unmatched pool
            result.unmatched_gateway.extend(gw_list[1:])
            result.unmatched_bank.extend(bank_list[1:])
        else:
            # No bank counterpart for this ref → all unmatched
            result.unmatched_gateway.extend(gw_list)

    # Bank records whose ref was never seen in gateway
    for ref, bank_list in bank_by_ref.items():
        if ref not in matched_refs:
            result.unmatched_bank.extend(bank_list)

    logger.info(
        "Exact match: %d matched, %d gateway unmatched, %d bank unmatched.",
        len(result.matched),
        len(result.unmatched_gateway),
        len(result.unmatched_bank),
    )
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _group_by_ref(txs: list[Transaction]) -> dict[str, list[Transaction]]:
    groups: dict[str, list[Transaction]] = defaultdict(list)
    for tx in txs:
        groups[tx.reference_number].append(tx)
    return dict(groups)


def _discrepancy_notes(gw: Transaction, bank: Transaction) -> list[str]:
    """Note any non-reference discrepancies on an otherwise exact match."""
    notes: list[str] = []
    if abs(gw.amount - bank.amount) > 0.01:
        notes.append(
            f"Amount mismatch: gateway=₹{gw.amount:.2f}, bank=₹{bank.amount:.2f}"
        )
    if gw.date != bank.date:
        delta = abs((gw.date - bank.date).days)
        notes.append(
            f"Date mismatch: gateway={gw.date}, bank={bank.date} ({delta}d apart)"
        )
    if gw.merchant_name.lower() != bank.merchant_name.lower():
        notes.append(
            f"Merchant name mismatch: {gw.merchant_name!r} vs {bank.merchant_name!r}"
        )
    return notes
