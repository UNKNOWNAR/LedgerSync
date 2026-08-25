"""
Tests for reconciler.fuzzy_match — scoring and candidate selection.
"""

from __future__ import annotations

import datetime

import pytest

from reconciler.fuzzy_match import find_fuzzy_candidates, fuzzy_score
from reconciler.models import ReconciliationConfig, Transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_tx(
    tx_id: str,
    ref: str = "REF999",
    amount: float = 1000.0,
    date: str = "2026-03-15",
    merchant: str = "BigBasket",
    source: str = "gateway",
) -> Transaction:
    return Transaction(
        transaction_id=tx_id,
        amount=amount,
        date=datetime.date.fromisoformat(date),
        merchant_name=merchant,
        reference_number=ref,
        source=source,
    )


DEFAULT_CONFIG = ReconciliationConfig(
    date_gap_days=3,
    amount_variance_pct=2.0,
    merchant_similarity_threshold=80.0,
    date_weight=0.30,
    amount_weight=0.40,
    merchant_weight=0.30,
    min_candidate_score=0.50,
)


# ---------------------------------------------------------------------------
# Score tests
# ---------------------------------------------------------------------------


class TestFuzzyScore:
    def test_identical_transactions_score_one(self):
        gw = make_tx("GW001", source="gateway")
        bank = make_tx("BK001", source="bank")
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        assert abs(score - 1.0) < 1e-4

    def test_zero_amount_both_sides(self):
        gw = make_tx("GW001", amount=0.0, source="gateway")
        bank = make_tx("BK001", amount=0.0, source="bank")
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        assert score > 0.9  # date and merchant perfect

    def test_date_within_threshold_reduces_score(self):
        gw = make_tx("GW001", date="2026-03-15", source="gateway")
        bank = make_tx("BK001", date="2026-03-17", source="bank")  # 2 days apart
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        assert 0.5 < score < 1.0

    def test_date_beyond_threshold_scores_zero_on_date_component(self):
        gw = make_tx("GW001", date="2026-03-15", source="gateway")
        bank = make_tx("BK001", date="2026-03-25", source="bank")  # 10 days, way beyond 3
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        # Date component is 0, amount/merchant might still be 1
        assert score < 0.80

    def test_amount_within_threshold(self):
        gw = make_tx("GW001", amount=1000.0, source="gateway")
        bank = make_tx("BK001", amount=985.0, source="bank")  # 1.5% variance
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        # date_score=1.0 (0.3 weight), amount_score>0 (0.4 weight), merchant=1.0 (0.3 weight)
        # amount component: 1 - 1.5/2.0 = 0.25, total = 0.3 + 0.1 + 0.3 = 0.70
        assert score > 0.65

    def test_amount_beyond_threshold_reduces_score(self):
        gw = make_tx("GW001", amount=1000.0, source="gateway")
        bank = make_tx("BK001", amount=960.0, source="bank")  # 4% variance
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        assert score < 0.80

    def test_merchant_similar_name(self):
        gw = make_tx("GW001", merchant="Swiggy Food Delivery", source="gateway")
        bank = make_tx("BK001", merchant="Swiggy Fud Delivery", source="bank")
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        assert score > 0.8

    def test_completely_different_merchants_lower_score(self):
        gw = make_tx("GW001", merchant="BigBasket", source="gateway")
        bank = make_tx("BK001", merchant="IndiGo Airlines", source="bank")
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        # Merchant score will be low; date+amount are fine
        assert score < 0.85

    def test_score_clamped_between_0_and_1(self):
        gw = make_tx("GW001", source="gateway")
        bank = make_tx("BK001", source="bank")
        score = fuzzy_score(gw, bank, DEFAULT_CONFIG)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Candidate selection tests
# ---------------------------------------------------------------------------


class TestFindFuzzyCandidates:
    def test_high_similarity_pair_selected(self):
        gw = [make_tx("GW001", amount=1000.0, date="2026-03-15", source="gateway")]
        bank = [make_tx("BK001", amount=985.0, date="2026-03-16", source="bank")]

        candidates = find_fuzzy_candidates(gw, bank, DEFAULT_CONFIG)
        assert len(candidates) == 1
        assert candidates[0].composite_score >= DEFAULT_CONFIG.min_candidate_score

    def test_low_similarity_pair_not_selected(self):
        gw = [make_tx("GW001", amount=1000.0, date="2026-03-15", merchant="BigBasket", source="gateway")]
        # Wildly different: amount, date, merchant all wrong
        bank = [make_tx("BK001", amount=50000.0, date="2026-06-01", merchant="IndiGo Airlines", source="bank")]

        candidates = find_fuzzy_candidates(gw, bank, DEFAULT_CONFIG)
        assert len(candidates) == 0

    def test_greedy_best_match_per_gateway(self):
        """Each gateway record should match at most one bank record."""
        gw = [make_tx("GW001", amount=1000.0, date="2026-03-15", source="gateway")]
        bank = [
            make_tx("BK001", amount=1000.0, date="2026-03-15", source="bank"),
            make_tx("BK002", amount=990.0, date="2026-03-16", source="bank"),
        ]
        candidates = find_fuzzy_candidates(gw, bank, DEFAULT_CONFIG)
        assert len(candidates) == 1  # best match only

    def test_empty_inputs_return_empty(self):
        assert find_fuzzy_candidates([], [], DEFAULT_CONFIG) == []

    def test_multiple_independent_pairs(self):
        gw = [
            make_tx("GW001", amount=1000.0, date="2026-03-15", merchant="BigBasket", source="gateway"),
            make_tx("GW002", amount=2000.0, date="2026-04-10", merchant="Swiggy Food Delivery", source="gateway"),
        ]
        bank = [
            make_tx("BK001", amount=985.0, date="2026-03-16", merchant="BigBasket", source="bank"),
            make_tx("BK002", amount=1963.0, date="2026-04-11", merchant="Swiggy Fud Delivery", source="bank"),
        ]
        candidates = find_fuzzy_candidates(gw, bank, DEFAULT_CONFIG)
        assert len(candidates) == 2

    def test_discrepancy_notes_populated(self):
        # Use same amount + close date so composite score is above 0.5, but with merchant mismatch
        gw = [make_tx("GW001", amount=1000.0, date="2026-03-15", merchant="Kalyan Jewellers", source="gateway")]
        bank = [make_tx("BK001", amount=1000.0, date="2026-03-16", merchant="Kalyan Jwellers", source="bank")]
        candidates = find_fuzzy_candidates(gw, bank, DEFAULT_CONFIG)
        assert len(candidates) == 1
        notes = candidates[0].discrepancy_notes
        # Should have notes about date and merchant (amount is same)
        assert any("date" in n.lower() for n in notes)
        assert any("merchant" in n.lower() for n in notes)
