"""
End-to-end pipeline tests with mocked LLM.
"""

from __future__ import annotations

import csv
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reconciler.models import LLMResult, MatchStatus, ReconciliationConfig
from reconciler.pipeline import run_pipeline


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

COLUMNS = ["transaction_id", "amount", "date", "merchant_name", "reference_number"]


def write_csv(tmp_path: Path, name: str, rows: list[dict]) -> Path:
    path = tmp_path / name
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def row(tx_id, amount, date, merchant, ref):
    return {
        "transaction_id": tx_id,
        "amount": str(amount),
        "date": date,
        "merchant_name": merchant,
        "reference_number": ref,
    }


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------

def mock_llm_match(pair, config) -> LLMResult:
    """Always returns a 'match' with high confidence."""
    return LLMResult(
        available=True,
        confidence=0.92,
        decision="match",
        reasoning="Mocked LLM: records match.",
    )


def mock_llm_partial(pair, config) -> LLMResult:
    """Always returns a 'partial' match."""
    return LLMResult(
        available=True,
        confidence=0.70,
        decision="partial",
        reasoning="Mocked LLM: partial match with discrepancies.",
    )


def mock_llm_exception(pair, config) -> LLMResult:
    """Always returns an exception."""
    return LLMResult(
        available=True,
        confidence=0.20,
        decision="exception",
        reasoning="Mocked LLM: not the same transaction.",
    )


def mock_llm_unavailable(pair, config) -> LLMResult:
    """Simulates LLM unavailability."""
    return LLMResult(
        available=False,
        confidence=pair.composite_score,
        decision="match" if pair.composite_score >= 0.85 else "partial",
        reasoning="LLM-unavailable, rule-based only.",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPipelineExactMatches:
    def test_all_exact_matches(self, tmp_path):
        rows_gw = [row(f"GW{i:03d}", 1000+i, "2026-03-15", "BigBasket", f"REF{i:012d}") for i in range(5)]
        rows_bank = [row(f"BK{i:03d}", 1000+i, "2026-03-15", "BigBasket", f"REF{i:012d}") for i in range(5)]

        gw_path = write_csv(tmp_path, "gw.csv", rows_gw)
        bank_path = write_csv(tmp_path, "bank.csv", rows_bank)

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        assert len(result.matched) == 5
        assert all(m.status == MatchStatus.EXACT for m in result.matched)
        assert len(result.partial_matches) == 0
        assert len(result.exceptions) == 0


class TestPipelineFuzzyMatches:
    @patch("reconciler.pipeline.reason_match", side_effect=mock_llm_match)
    def test_fuzzy_match_with_date_delay(self, mock_llm, tmp_path):
        rows_gw = [row("GW001", 1500.0, "2026-03-15", "Swiggy Food Delivery", "REF_UNIQUE_001")]
        rows_bank = [row("BK001", 1500.0, "2026-03-17", "Swiggy Food Delivery", "REF_UNIQ_BANK")]  # diff ref, 2d late

        gw_path = write_csv(tmp_path, "gw.csv", rows_gw)
        bank_path = write_csv(tmp_path, "bank.csv", rows_bank)

        config = ReconciliationConfig(date_gap_days=3, llm_enabled=True)
        result = run_pipeline(gw_path, bank_path, config)

        # Should be caught by fuzzy + LLM confirmed as match
        assert len(result.matched) + len(result.partial_matches) >= 1

    @patch("reconciler.pipeline.reason_match", side_effect=mock_llm_partial)
    def test_fuzzy_partial_goes_to_partial_matches(self, mock_llm, tmp_path):
        rows_gw = [row("GW001", 1000.0, "2026-03-15", "Kalyan Jewellers", "REF_UNIQUE_002")]
        rows_bank = [row("BK001", 985.0, "2026-03-16", "Kalyan Jwellers", "REF_BANK_ONLY")]

        gw_path = write_csv(tmp_path, "gw.csv", rows_gw)
        bank_path = write_csv(tmp_path, "bank.csv", rows_bank)

        config = ReconciliationConfig(llm_enabled=True)
        result = run_pipeline(gw_path, bank_path, config)

        assert len(result.partial_matches) >= 1


class TestPipelineExceptions:
    def test_gateway_only_record_is_exception(self, tmp_path):
        rows_gw = [row("GW001", 1000.0, "2026-03-15", "BigBasket", "REF_GW_ONLY")]
        rows_bank: list[dict] = []  # no bank records at all

        gw_path = write_csv(tmp_path, "gw.csv", rows_gw)
        bank_path = write_csv(tmp_path, "bank.csv", rows_bank)

        # Empty bank CSV needs header
        bank_path.write_text(
            "transaction_id,amount,date,merchant_name,reference_number\n",
            encoding="utf-8",
        )

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        assert len(result.exceptions) == 1
        assert result.exceptions[0].gateway_tx is not None
        assert result.exceptions[0].bank_tx is None

    def test_bank_only_record_is_exception(self, tmp_path):
        rows_bank = [row("BK001", 1000.0, "2026-03-15", "BigBasket", "REF_BANK_ONLY")]

        gw_path = tmp_path / "gw.csv"
        gw_path.write_text(
            "transaction_id,amount,date,merchant_name,reference_number\n",
            encoding="utf-8",
        )
        bank_path = write_csv(tmp_path, "bank.csv", rows_bank)

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        assert len(result.exceptions) == 1
        assert result.exceptions[0].bank_tx is not None
        assert result.exceptions[0].gateway_tx is None


class TestPipelineLLMFallback:
    @patch("reconciler.pipeline.reason_match", side_effect=mock_llm_unavailable)
    def test_llm_unavailable_uses_rule_score(self, mock_llm, tmp_path):
        rows_gw = [row("GW001", 1000.0, "2026-03-15", "BigBasket", "REF_FUZZY_001")]
        rows_bank = [row("BK001", 985.0, "2026-03-16", "BigBasket", "REF_BANK_FUZZY")]

        gw_path = write_csv(tmp_path, "gw.csv", rows_gw)
        bank_path = write_csv(tmp_path, "bank.csv", rows_bank)

        config = ReconciliationConfig(llm_enabled=True)
        result = run_pipeline(gw_path, bank_path, config)

        # All matched/partial should have llm_available=False
        for m in result.matched + result.partial_matches:
            assert not m.llm_available
            assert "LLM-unavailable" in m.llm_reasoning


class TestPipelineIngestionErrors:
    def test_ingestion_errors_surface_as_exceptions(self, tmp_path):
        bad_rows = [
            {  # malformed date
                "transaction_id": "GW_BAD",
                "amount": "1000",
                "date": "not-a-date",
                "merchant_name": "BigBasket",
                "reference_number": "REF_BAD",
            }
        ]
        gw_path = write_csv(tmp_path, "gw.csv", bad_rows)
        bank_path = tmp_path / "bank.csv"
        bank_path.write_text(
            "transaction_id,amount,date,merchant_name,reference_number\n",
            encoding="utf-8",
        )

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        assert len(result.ingestion_errors) == 1
        # Ingestion errors should surface in exception list
        ingestion_exceptions = [
            m for m in result.exceptions
            if "ingestion error" in " ".join(m.discrepancy_notes).lower()
        ]
        assert len(ingestion_exceptions) == 1

    def test_pipeline_does_not_crash_on_mixed_bad_and_good_rows(self, tmp_path):
        rows = [
            row("GW001", 1000.0, "2026-03-15", "BigBasket", "REF001"),
            {
                "transaction_id": "GW002",
                "amount": "",
                "date": "2026-03-15",
                "merchant_name": "BigBasket",
                "reference_number": "REF002",
            },
            row("GW003", 2000.0, "2026-04-01", "Swiggy Food Delivery", "REF003"),
        ]
        bank_rows = [row("BK001", 1000.0, "2026-03-15", "BigBasket", "REF001")]

        gw_path = tmp_path / "gw.csv"
        with gw_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        bank_path = write_csv(tmp_path, "bank.csv", bank_rows)

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        # GW001 should match exactly
        assert any(
            m.gateway_tx and m.gateway_tx.transaction_id == "GW001"
            for m in result.matched
        )
        # GW002 ingestion error
        assert len(result.ingestion_errors) == 1
        # Pipeline didn't crash
        assert result is not None
