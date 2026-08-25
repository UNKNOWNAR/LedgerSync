"""
Tests for reconciler.ingest — CSV loading and validation.
"""

from __future__ import annotations

import csv
import datetime
import io
import textwrap
from pathlib import Path

import pytest

from reconciler.ingest import load_csv
from reconciler.models import Transaction


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


def write_csv(tmp_path: Path, filename: str, rows: list[dict]) -> Path:
    """Write a list of dicts to a CSV file in tmp_path."""
    path = tmp_path / filename
    if not rows:
        path.write_text(
            "transaction_id,amount,date,merchant_name,reference_number\n",
            encoding="utf-8",
        )
        return path
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


VALID_ROW = {
    "transaction_id": "TX001",
    "amount": "1500.00",
    "date": "2026-03-15",
    "merchant_name": "BigBasket",
    "reference_number": "REF123456789012",
}


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestLoadCsvHappyPath:
    def test_valid_single_row(self, tmp_path):
        path = write_csv(tmp_path, "gw.csv", [VALID_ROW])
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 1
        assert len(errors) == 0
        tx = txs[0]
        assert isinstance(tx, Transaction)
        assert tx.transaction_id == "TX001"
        assert tx.amount == 1500.00
        assert tx.date == datetime.date(2026, 3, 15)
        assert tx.merchant_name == "BigBasket"
        assert tx.reference_number == "REF123456789012"
        assert tx.source == "gateway"

    def test_multiple_valid_rows(self, tmp_path):
        rows = [
            {**VALID_ROW, "transaction_id": f"TX{i:03d}", "reference_number": f"REF{i:012d}"}
            for i in range(1, 11)
        ]
        path = write_csv(tmp_path, "gw.csv", rows)
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 10
        assert len(errors) == 0

    def test_source_label_bank(self, tmp_path):
        path = write_csv(tmp_path, "bank.csv", [VALID_ROW])
        txs, _ = load_csv(path, source="bank")
        assert txs[0].source == "bank"

    def test_amount_with_commas_and_rupee_symbol(self, tmp_path):
        row = {**VALID_ROW, "amount": "₹1,50,000.00"}
        path = write_csv(tmp_path, "gw.csv", [row])
        txs, errors = load_csv(path, source="gateway")
        assert len(errors) == 0
        assert txs[0].amount == 150000.00

    def test_date_formats(self, tmp_path):
        date_variants = [
            ("2026-03-15", datetime.date(2026, 3, 15), "iso"),
            ("15-03-2026", datetime.date(2026, 3, 15), "dmy_dash"),
            ("15/03/2026", datetime.date(2026, 3, 15), "dmy_slash"),
        ]
        for raw_date, expected, label in date_variants:
            row = {**VALID_ROW, "date": raw_date, "transaction_id": f"TX_{label}"}
            path = write_csv(tmp_path, f"gw_{label}.csv", [row])
            txs, errors = load_csv(path, source="gateway")
            assert len(errors) == 0, f"Unexpected error for date '{raw_date}': {errors}"
            assert txs[0].date == expected

    def test_empty_file_returns_empty_lists(self, tmp_path):
        path = write_csv(tmp_path, "empty.csv", [])
        txs, errors = load_csv(path, source="gateway")
        assert txs == []
        assert errors == []


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_missing_required_column_raises(self, tmp_path):
        row = {k: v for k, v in VALID_ROW.items() if k != "amount"}  # drop amount
        path = write_csv(tmp_path, "bad.csv", [row])
        with pytest.raises(ValueError, match="missing required columns"):
            load_csv(path, source="gateway")

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_csv(tmp_path / "nonexistent.csv", source="gateway")


# ---------------------------------------------------------------------------
# Row-level error capture tests
# ---------------------------------------------------------------------------


class TestRowLevelErrors:
    def test_missing_transaction_id_captured(self, tmp_path):
        row = {**VALID_ROW, "transaction_id": ""}
        path = write_csv(tmp_path, "gw.csv", [row])
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 0
        assert len(errors) == 1
        assert "transaction_id" in errors[0].reason.lower()

    def test_missing_amount_captured(self, tmp_path):
        row = {**VALID_ROW, "amount": ""}
        path = write_csv(tmp_path, "gw.csv", [row])
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 0
        assert len(errors) == 1
        assert "amount" in errors[0].reason.lower()

    def test_malformed_amount_captured(self, tmp_path):
        row = {**VALID_ROW, "amount": "not_a_number"}
        path = write_csv(tmp_path, "gw.csv", [row])
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 0
        assert len(errors) == 1
        assert "malformed amount" in errors[0].reason.lower()

    def test_malformed_date_captured(self, tmp_path):
        row = {**VALID_ROW, "date": "2026-99-99"}
        path = write_csv(tmp_path, "gw.csv", [row])
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 0
        assert len(errors) == 1
        assert "malformed date" in errors[0].reason.lower()

    def test_good_and_bad_rows_separated(self, tmp_path):
        rows = [
            VALID_ROW,
            {**VALID_ROW, "transaction_id": "TX002", "amount": "", "reference_number": "REF000000000002"},
            {**VALID_ROW, "transaction_id": "TX003", "reference_number": "REF000000000003"},
        ]
        path = write_csv(tmp_path, "gw.csv", rows)
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 2
        assert len(errors) == 1


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


class TestDuplicateDetection:
    def test_duplicate_transaction_id_captured(self, tmp_path):
        rows = [
            VALID_ROW,
            {**VALID_ROW, "reference_number": "REF999999999999"},  # same tx_id, different ref
        ]
        path = write_csv(tmp_path, "gw.csv", rows)
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 1   # first occurrence accepted
        assert len(errors) == 1
        assert "duplicate" in errors[0].reason.lower()

    def test_unique_ids_all_accepted(self, tmp_path):
        rows = [
            {**VALID_ROW, "transaction_id": f"TX{i}", "reference_number": f"REF{i:012d}"}
            for i in range(5)
        ]
        path = write_csv(tmp_path, "gw.csv", rows)
        txs, errors = load_csv(path, source="gateway")
        assert len(txs) == 5
        assert len(errors) == 0
