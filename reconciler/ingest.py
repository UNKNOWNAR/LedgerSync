"""
CSV ingestion and validation for the reconciliation pipeline.

Public API
----------
load_csv(path, source) -> tuple[list[Transaction], list[IngestionError]]

The function is deliberately lenient: bad rows are captured as IngestionError
objects and returned alongside valid Transaction objects, so the pipeline can
continue on valid data while surfacing failures in the exception report.
"""

from __future__ import annotations

import csv
import datetime
import logging
from pathlib import Path
from typing import Optional

from .models import IngestionError, Transaction

logger = logging.getLogger(__name__)

# Required column names (case-insensitive matching applied at load time)
REQUIRED_COLUMNS = {
    "transaction_id",
    "amount",
    "date",
    "merchant_name",
    "reference_number",
}

# Accepted date formats — tried in order
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_csv(
    path: str | Path,
    source: str,
) -> tuple[list[Transaction], list[IngestionError]]:
    """
    Load and validate a transaction CSV file.

    Parameters
    ----------
    path   : path to the CSV file
    source : label attached to every Transaction ("gateway" | "bank")

    Returns
    -------
    transactions  : successfully parsed Transaction objects
    errors        : rows that failed validation / parsing
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    rows = _read_raw_csv(path)
    if not rows:
        logger.warning("CSV file %s is empty.", path)
        return [], []

    # Normalise column names
    normalised_rows = [_normalise_keys(row) for row in rows]

    # Check schema
    _check_schema(normalised_rows[0], path)

    transactions: list[Transaction] = []
    errors: list[IngestionError] = []
    seen_ids: dict[str, int] = {}   # transaction_id -> first row index

    for idx, row in enumerate(normalised_rows):
        tx, error = _parse_row(row, idx, source)
        if error:
            errors.append(error)
            continue

        # Duplicate transaction_id check (within the same file)
        assert tx is not None
        if tx.transaction_id in seen_ids:
            first_seen = seen_ids[tx.transaction_id]
            errors.append(
                IngestionError(
                    source=source,
                    row_index=idx,
                    raw_data=row,
                    reason=(
                        f"Duplicate transaction_id '{tx.transaction_id}' "
                        f"(first seen at row {first_seen})"
                    ),
                )
            )
            logger.warning(
                "Duplicate transaction_id '%s' at row %d in %s (first at row %d).",
                tx.transaction_id,
                idx,
                path.name,
                first_seen,
            )
            continue

        seen_ids[tx.transaction_id] = idx
        transactions.append(tx)

    logger.info(
        "Loaded %d transactions from '%s' (%d ingestion errors).",
        len(transactions),
        path.name,
        len(errors),
    )
    return transactions, errors


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_raw_csv(path: Path) -> list[dict]:
    """Read the CSV file and return a list of raw row dicts."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def _normalise_keys(row: dict) -> dict:
    """Lower-case and strip all column names."""
    return {k.strip().lower(): v.strip() if isinstance(v, str) else v for k, v in row.items()}


def _check_schema(sample_row: dict, path: Path) -> None:
    """Raise ValueError if required columns are missing."""
    missing = REQUIRED_COLUMNS - set(sample_row.keys())
    if missing:
        raise ValueError(
            f"CSV '{path.name}' is missing required columns: {sorted(missing)}"
        )


def _parse_row(
    row: dict,
    idx: int,
    source: str,
) -> tuple[Optional[Transaction], Optional[IngestionError]]:
    """
    Attempt to parse a single CSV row into a Transaction.
    Returns (Transaction, None) on success or (None, IngestionError) on failure.
    """
    # --- transaction_id ---
    tx_id = row.get("transaction_id", "").strip()
    if not tx_id:
        return None, IngestionError(
            source=source,
            row_index=idx,
            raw_data=row,
            reason="Missing or empty transaction_id",
        )

    # --- amount ---
    raw_amount = row.get("amount", "").strip()
    if not raw_amount:
        return None, IngestionError(
            source=source,
            row_index=idx,
            raw_data=row,
            reason=f"Missing amount for transaction_id='{tx_id}'",
        )
    try:
        # Remove currency symbols / commas common in Indian formatted numbers
        cleaned_amount = raw_amount.replace("₹", "").replace(",", "").strip()
        amount = float(cleaned_amount)
    except ValueError:
        return None, IngestionError(
            source=source,
            row_index=idx,
            raw_data=row,
            reason=f"Malformed amount '{raw_amount}' for transaction_id='{tx_id}'",
        )

    # --- date ---
    raw_date = row.get("date", "").strip()
    parsed_date = _parse_date(raw_date)
    if parsed_date is None:
        return None, IngestionError(
            source=source,
            row_index=idx,
            raw_data=row,
            reason=(
                f"Malformed date '{raw_date}' for transaction_id='{tx_id}'. "
                f"Accepted formats: {DATE_FORMATS}"
            ),
        )

    # --- merchant_name ---
    merchant = row.get("merchant_name", "").strip()
    if not merchant:
        return None, IngestionError(
            source=source,
            row_index=idx,
            raw_data=row,
            reason=f"Missing merchant_name for transaction_id='{tx_id}'",
        )

    # --- reference_number ---
    ref = row.get("reference_number", "").strip()
    if not ref:
        return None, IngestionError(
            source=source,
            row_index=idx,
            raw_data=row,
            reason=f"Missing reference_number for transaction_id='{tx_id}'",
        )

    tx = Transaction(
        transaction_id=tx_id,
        amount=amount,
        date=parsed_date,
        merchant_name=merchant,
        reference_number=ref,
        source=source,
    )
    return tx, None


def _parse_date(raw: str) -> Optional[datetime.date]:
    """Try each accepted date format; return None if all fail."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None
