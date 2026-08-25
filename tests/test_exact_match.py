"""
Tests for reconciler.exact_match.
"""

from __future__ import annotations

import datetime

import pytest

from reconciler.exact_match import exact_match
from reconciler.models import MatchStatus, Transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_tx(
    tx_id: str,
    ref: str,
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExactMatch:
    def test_single_perfect_match(self):
        gw = [make_tx("GW001", "REF001", source="gateway")]
        bank = [make_tx("BK001", "REF001", source="bank")]
        result = exact_match(gw, bank)

        assert len(result.matched) == 1
        assert len(result.unmatched_gateway) == 0
        assert len(result.unmatched_bank) == 0

        m = result.matched[0]
        assert m.status == MatchStatus.EXACT
        assert m.confidence == 1.0
        assert m.gateway_tx.transaction_id == "GW001"
        assert m.bank_tx.transaction_id == "BK001"

    def test_multiple_perfect_matches(self):
        gw = [make_tx(f"GW{i:03d}", f"REF{i:03d}", source="gateway") for i in range(10)]
        bank = [make_tx(f"BK{i:03d}", f"REF{i:03d}", source="bank") for i in range(10)]
        result = exact_match(gw, bank)

        assert len(result.matched) == 10
        assert len(result.unmatched_gateway) == 0
        assert len(result.unmatched_bank) == 0

    def test_no_matches(self):
        gw = [make_tx("GW001", "REF001", source="gateway")]
        bank = [make_tx("BK001", "REF999", source="bank")]
        result = exact_match(gw, bank)

        assert len(result.matched) == 0
        assert len(result.unmatched_gateway) == 1
        assert len(result.unmatched_bank) == 1

    def test_partial_match(self):
        gw = [
            make_tx("GW001", "REF001", source="gateway"),
            make_tx("GW002", "REF002", source="gateway"),  # no bank counterpart
        ]
        bank = [make_tx("BK001", "REF001", source="bank")]
        result = exact_match(gw, bank)

        assert len(result.matched) == 1
        assert len(result.unmatched_gateway) == 1
        assert result.unmatched_gateway[0].transaction_id == "GW002"
        assert len(result.unmatched_bank) == 0

    def test_amount_discrepancy_noted_on_exact_ref_match(self):
        gw = [make_tx("GW001", "REF001", amount=1000.0, source="gateway")]
        bank = [make_tx("BK001", "REF001", amount=980.0, source="bank")]
        result = exact_match(gw, bank)

        assert len(result.matched) == 1
        m = result.matched[0]
        assert m.status == MatchStatus.EXACT   # still exact (same ref)
        assert any("amount mismatch" in n.lower() for n in m.discrepancy_notes)

    def test_date_discrepancy_noted_on_exact_ref_match(self):
        gw = [make_tx("GW001", "REF001", date="2026-03-15", source="gateway")]
        bank = [make_tx("BK001", "REF001", date="2026-03-17", source="bank")]
        result = exact_match(gw, bank)

        assert len(result.matched) == 1
        m = result.matched[0]
        assert any("date mismatch" in n.lower() for n in m.discrepancy_notes)

    def test_duplicate_ref_in_gateway_extras_to_unmatched(self):
        """If gateway has two records with the same ref, first matches, second is unmatched."""
        gw = [
            make_tx("GW001", "REF001", source="gateway"),
            make_tx("GW002", "REF001", source="gateway"),  # duplicate ref
        ]
        bank = [make_tx("BK001", "REF001", source="bank")]
        result = exact_match(gw, bank)

        assert len(result.matched) == 1
        assert len(result.unmatched_gateway) == 1
        assert result.unmatched_gateway[0].transaction_id == "GW002"

    def test_empty_inputs(self):
        result = exact_match([], [])
        assert result.matched == []
        assert result.unmatched_gateway == []
        assert result.unmatched_bank == []

    def test_gateway_only(self):
        gw = [make_tx("GW001", "REF001", source="gateway")]
        result = exact_match(gw, [])
        assert len(result.matched) == 0
        assert len(result.unmatched_gateway) == 1

    def test_bank_only(self):
        bank = [make_tx("BK001", "REF001", source="bank")]
        result = exact_match([], bank)
        assert len(result.matched) == 0
        assert len(result.unmatched_bank) == 1
