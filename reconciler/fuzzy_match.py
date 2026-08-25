"""
Fuzzy matching stage of the reconciliation pipeline.

Scoring
-------
A composite score (0–1) is computed for every candidate pair from three
independent signals:

  date_score     = max(0, 1 - |date_diff_days| / date_gap_days)
  amount_score   = max(0, 1 - |pct_diff| / amount_variance_pct)
  merchant_score = rapidfuzz.fuzz.token_sort_ratio(a, b) / 100.0

  composite = (date_weight   * date_score
             + amount_weight * amount_score
             + merchant_weight * merchant_score)

Only pairs whose composite score ≥ config.min_candidate_score are returned
as candidates for the LLM reasoning step.

Public API
----------
find_fuzzy_candidates(unmatched_gw, unmatched_bank, config)
    -> list[CandidatePair]

fuzzy_score(t1, t2, config) -> float
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from rapidfuzz import fuzz

from .models import ReconciliationConfig, Transaction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Candidate pair
# ---------------------------------------------------------------------------


@dataclass
class CandidatePair:
    """A gateway/bank pair that passed the minimum fuzzy threshold."""

    gateway_tx: Transaction
    bank_tx: Transaction
    composite_score: float
    date_score: float
    amount_score: float
    merchant_score: float
    discrepancy_notes: list[str]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def find_fuzzy_candidates(
    unmatched_gw: list[Transaction],
    unmatched_bank: list[Transaction],
    config: ReconciliationConfig,
) -> list[CandidatePair]:
    """
    Compare every unmatched gateway transaction against every unmatched bank
    transaction and return pairs above the minimum composite threshold.

    For each gateway record we keep only the single best-scoring bank
    candidate (greedy assignment).  This avoids many-to-one pairings.
    """
    candidates: list[CandidatePair] = []

    for gw_tx in unmatched_gw:
        best: CandidatePair | None = None

        for bank_tx in unmatched_bank:
            pair = _score_pair(gw_tx, bank_tx, config)
            if pair.composite_score >= config.min_candidate_score:
                if best is None or pair.composite_score > best.composite_score:
                    best = pair

        if best is not None:
            candidates.append(best)

    logger.info(
        "Fuzzy stage: %d candidates from %d gw × %d bank unmatched records.",
        len(candidates),
        len(unmatched_gw),
        len(unmatched_bank),
    )
    return candidates


def fuzzy_score(
    t1: Transaction,
    t2: Transaction,
    config: ReconciliationConfig,
) -> float:
    """Return the composite fuzzy score (0–1) for a transaction pair."""
    return _score_pair(t1, t2, config).composite_score


# ---------------------------------------------------------------------------
# Internal scoring
# ---------------------------------------------------------------------------


def _score_pair(
    gw: Transaction,
    bank: Transaction,
    config: ReconciliationConfig,
) -> CandidatePair:
    date_s = _date_score(gw, bank, config)
    amount_s = _amount_score(gw, bank, config)
    merchant_s = _merchant_score(gw, bank)

    composite = (
        config.date_weight * date_s
        + config.amount_weight * amount_s
        + config.merchant_weight * merchant_s
    )
    composite = round(min(max(composite, 0.0), 1.0), 6)

    notes = _build_notes(gw, bank, date_s, amount_s, merchant_s, config)

    return CandidatePair(
        gateway_tx=gw,
        bank_tx=bank,
        composite_score=composite,
        date_score=date_s,
        amount_score=amount_s,
        merchant_score=merchant_s,
        discrepancy_notes=notes,
    )


def _date_score(
    gw: Transaction,
    bank: Transaction,
    config: ReconciliationConfig,
) -> float:
    diff_days = abs((gw.date - bank.date).days)
    if config.date_gap_days == 0:
        return 1.0 if diff_days == 0 else 0.0
    return max(0.0, 1.0 - diff_days / config.date_gap_days)


def _amount_score(
    gw: Transaction,
    bank: Transaction,
    config: ReconciliationConfig,
) -> float:
    if gw.amount == 0 and bank.amount == 0:
        return 1.0
    base = max(abs(gw.amount), abs(bank.amount))
    pct_diff = abs(gw.amount - bank.amount) / base * 100.0
    if config.amount_variance_pct == 0:
        return 1.0 if pct_diff == 0 else 0.0
    return max(0.0, 1.0 - pct_diff / config.amount_variance_pct)


def _merchant_score(gw: Transaction, bank: Transaction) -> float:
    """RapidFuzz token_sort_ratio normalised to 0–1."""
    ratio = fuzz.token_sort_ratio(
        gw.merchant_name.lower(),
        bank.merchant_name.lower(),
    )
    return ratio / 100.0


def _build_notes(
    gw: Transaction,
    bank: Transaction,
    date_s: float,
    amount_s: float,
    merchant_s: float,
    config: ReconciliationConfig,
) -> list[str]:
    notes: list[str] = []

    date_diff = abs((gw.date - bank.date).days)
    if date_diff > 0:
        notes.append(
            f"Date gap: {date_diff}d "
            f"(gateway={gw.date}, bank={bank.date})"
        )

    base = max(abs(gw.amount), abs(bank.amount), 1e-9)
    pct_diff = abs(gw.amount - bank.amount) / base * 100.0
    if pct_diff > 0.01:
        notes.append(
            f"Amount variance: {pct_diff:.2f}% "
            f"(gateway=₹{gw.amount:.2f}, bank=₹{bank.amount:.2f})"
        )

    merchant_ratio = merchant_s * 100.0
    if merchant_ratio < 100.0:
        notes.append(
            f"Merchant similarity: {merchant_ratio:.1f}% "
            f"({gw.merchant_name!r} vs {bank.merchant_name!r})"
        )

    return notes
