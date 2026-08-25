"""
Prompt 6 — Deliberate failure injection test suite.

Each test injects a specific edge case into the pipeline and verifies:
1. The system does NOT crash.
2. The error is logged / captured clearly.
3. The error surfaces in the exception report with a human-readable reason.

Edge cases tested
-----------------
1. Malformed date in gateway file
2. Missing amount field (empty string) in bank file
3. Duplicate transaction_id within the same file
4. Both files completely empty (headers only)
5. Missing required column (schema error) — should raise, not silently skip
6. Amount as non-numeric string (e.g. "N/A")
7. Mixed: one good row + one bad row; good row should still match
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from reconciler.ingest import load_csv
from reconciler.models import MatchStatus, ReconciliationConfig
from reconciler.pipeline import run_pipeline

COLUMNS = ["transaction_id", "amount", "date", "merchant_name", "reference_number"]


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def write_raw_csv(path: Path, rows: list[dict], fieldnames=None) -> Path:
    if fieldnames is None:
        fieldnames = COLUMNS
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def empty_csv(path: Path) -> Path:
    path.write_text(
        "transaction_id,amount,date,merchant_name,reference_number\n",
        encoding="utf-8",
    )
    return path


def good_row(**overrides) -> dict:
    base = {
        "transaction_id": "GW001",
        "amount": "1000.00",
        "date": "2026-03-15",
        "merchant_name": "BigBasket",
        "reference_number": "REF000000000001",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Edge Case 1 — Malformed date
# ---------------------------------------------------------------------------


class TestMalformedDate:
    """A row with an unparseable date must be captured as an IngestionError."""

    def test_malformed_date_captured_not_crash(self, tmp_path):
        gw_path = write_raw_csv(
            tmp_path / "gw.csv",
            [good_row(date="32-13-2026")],  # completely invalid date
        )
        bank_path = empty_csv(tmp_path / "bank.csv")

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)  # must NOT raise

        assert len(result.ingestion_errors) == 1
        assert "malformed date" in result.ingestion_errors[0].reason.lower()

    def test_malformed_date_surfaces_in_exception_report(self, tmp_path):
        gw_path = write_raw_csv(
            tmp_path / "gw.csv",
            [good_row(date="BADDATE")],
        )
        bank_path = empty_csv(tmp_path / "bank.csv")

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        # Ingestion error should appear as an exception with a clear note
        exception_notes = [
            note
            for m in result.exceptions
            for note in m.discrepancy_notes
        ]
        assert any("ingestion error" in n.lower() for n in exception_notes)

    def test_malformed_date_row_index_recorded(self, tmp_path):
        rows = [
            good_row(transaction_id="GW001", reference_number="REF000000000001"),
            good_row(transaction_id="GW002", date="BADDATE", reference_number="REF000000000002"),
        ]
        gw_path = write_raw_csv(tmp_path / "gw.csv", rows)
        bank_path = empty_csv(tmp_path / "bank.csv")

        _, errors = load_csv(gw_path, source="gateway")
        assert len(errors) == 1
        assert errors[0].row_index == 1   # 0-indexed: second row


# ---------------------------------------------------------------------------
# Edge Case 2 — Missing amount field
# ---------------------------------------------------------------------------


class TestMissingAmountField:
    def test_empty_amount_captured(self, tmp_path):
        gw_path = empty_csv(tmp_path / "gw.csv")
        bank_path = write_raw_csv(
            tmp_path / "bank.csv",
            [good_row(transaction_id="BK001", amount="")],
        )

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        assert len(result.ingestion_errors) == 1
        assert "amount" in result.ingestion_errors[0].reason.lower()

    def test_non_numeric_amount_captured(self, tmp_path):
        gw_path = write_raw_csv(
            tmp_path / "gw.csv",
            [good_row(amount="N/A")],
        )
        bank_path = empty_csv(tmp_path / "bank.csv")

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        assert len(result.ingestion_errors) == 1
        assert "malformed amount" in result.ingestion_errors[0].reason.lower()

    def test_amount_error_does_not_crash_pipeline(self, tmp_path):
        gw_path = write_raw_csv(
            tmp_path / "gw.csv",
            [good_row(amount="not-a-float")],
        )
        bank_path = empty_csv(tmp_path / "bank.csv")

        # Should complete without raising
        result = run_pipeline(gw_path, bank_path, ReconciliationConfig(llm_enabled=False))
        assert result is not None


# ---------------------------------------------------------------------------
# Edge Case 3 — Duplicate transaction_id within one file
# ---------------------------------------------------------------------------


class TestDuplicateTransactionId:
    def test_duplicate_id_in_gateway_captured(self, tmp_path):
        rows = [
            good_row(transaction_id="GW001", reference_number="REF000000000001"),
            good_row(transaction_id="GW001", reference_number="REF000000000002"),  # duplicate id
        ]
        gw_path = write_raw_csv(tmp_path / "gw.csv", rows)
        bank_path = empty_csv(tmp_path / "bank.csv")

        _, errors = load_csv(gw_path, source="gateway")
        assert len(errors) == 1
        assert "duplicate" in errors[0].reason.lower()
        assert "GW001" in errors[0].reason

    def test_duplicate_id_pipeline_does_not_crash(self, tmp_path):
        rows = [
            good_row(transaction_id="GW001", reference_number="REF000000000001"),
            good_row(transaction_id="GW001", reference_number="REF000000000002"),
        ]
        gw_path = write_raw_csv(tmp_path / "gw.csv", rows)
        bank_path = write_raw_csv(
            tmp_path / "bank.csv",
            [good_row(transaction_id="BK001", reference_number="REF000000000001")],
        )

        result = run_pipeline(gw_path, bank_path, ReconciliationConfig(llm_enabled=False))
        assert result is not None
        # First GW001 should match BK001 exactly
        assert any(
            m.gateway_tx and m.gateway_tx.transaction_id == "GW001"
            for m in result.matched
        )

    def test_duplicate_flags_in_exception_report(self, tmp_path):
        rows = [
            good_row(transaction_id="GW-DUP", reference_number="REF000000000001"),
            good_row(transaction_id="GW-DUP", reference_number="REF000000000002"),
        ]
        gw_path = write_raw_csv(tmp_path / "gw.csv", rows)
        bank_path = empty_csv(tmp_path / "bank.csv")

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        exception_notes = [
            note
            for m in result.exceptions
            for note in m.discrepancy_notes
        ]
        assert any("ingestion error" in n.lower() for n in exception_notes)


# ---------------------------------------------------------------------------
# Edge Case 4 — Both files empty (headers only)
# ---------------------------------------------------------------------------


class TestBothFilesEmpty:
    def test_empty_files_return_empty_result(self, tmp_path):
        gw_path = empty_csv(tmp_path / "gw.csv")
        bank_path = empty_csv(tmp_path / "bank.csv")

        result = run_pipeline(gw_path, bank_path, ReconciliationConfig(llm_enabled=False))
        assert result.matched == []
        assert result.partial_matches == []
        assert result.exceptions == []
        assert result.ingestion_errors == []


# ---------------------------------------------------------------------------
# Edge Case 5 — Missing required column (schema violation)
# ---------------------------------------------------------------------------


class TestMissingRequiredColumn:
    def test_missing_column_raises_value_error(self, tmp_path):
        """Schema violations should raise ValueError — not silently skip."""
        path = tmp_path / "bad_schema.csv"
        # Write CSV without 'amount' column
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["transaction_id", "date", "merchant_name", "reference_number"],
            )
            writer.writeheader()
            writer.writerow({
                "transaction_id": "GW001",
                "date": "2026-03-15",
                "merchant_name": "BigBasket",
                "reference_number": "REF001",
            })

        with pytest.raises(ValueError, match="missing required columns"):
            load_csv(path, source="gateway")


# ---------------------------------------------------------------------------
# Edge Case 6 — Mixed good and bad rows: good row still matches
# ---------------------------------------------------------------------------


class TestMixedGoodAndBadRows:
    def test_good_row_matches_despite_bad_sibling(self, tmp_path):
        gw_rows = [
            good_row(transaction_id="GW001", reference_number="REF000000000001"),   # good
            good_row(transaction_id="GW002", amount="", reference_number="REF000000000002"),  # bad
        ]
        bank_rows = [
            good_row(transaction_id="BK001", reference_number="REF000000000001"),   # matches GW001
        ]
        gw_path = write_raw_csv(tmp_path / "gw.csv", gw_rows)
        bank_path = write_raw_csv(tmp_path / "bank.csv", bank_rows)

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        # GW001–BK001 match
        assert any(
            m.gateway_tx and m.gateway_tx.transaction_id == "GW001"
            for m in result.matched
        )
        # GW002 is an ingestion error
        assert len(result.ingestion_errors) == 1
        assert result.ingestion_errors[0].raw_data["transaction_id"] == "GW002"

    def test_error_reason_is_human_readable(self, tmp_path):
        gw_path = write_raw_csv(
            tmp_path / "gw.csv",
            [good_row(date="2026-99-01", transaction_id="GW_ERR")],  # bad date
        )
        bank_path = empty_csv(tmp_path / "bank.csv")

        config = ReconciliationConfig(llm_enabled=False)
        result = run_pipeline(gw_path, bank_path, config)

        # Check the reason string is human-readable
        reason = result.ingestion_errors[0].reason
        assert "GW_ERR" in reason
        assert "malformed date" in reason.lower()
        # Should mention the bad value
        assert "2026-99-01" in reason
