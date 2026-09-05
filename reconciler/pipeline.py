"""
Pipeline orchestrator — ties all reconciliation stages together.

Steps
-----
1. Ingest both CSVs (validation + error capture)
2. Exact match on reference_number
3. Fuzzy candidate generation for unmatched records
4. LLM reasoning for each candidate pair
5. Classify candidates → matched / partial_matches / exceptions
6. Any completely unmatched records → exceptions

Public API
----------
run_pipeline(gw_path, bank_path, config) -> ReconciliationResult
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path

from .exact_match import exact_match
from .fuzzy_match import CandidatePair, find_fuzzy_candidates
from .ingest import load_csv
from .llm_reasoning import reason_match
from .models import (
    IngestionError,
    MatchResult,
    MatchStatus,
    ReconciliationConfig,
    ReconciliationResult,
    Transaction,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_pipeline(
    gw_path: str | Path,
    bank_path: str | Path,
    config: ReconciliationConfig | None = None,
) -> ReconciliationResult:
    """
    Run the full reconciliation pipeline.

    Parameters
    ----------
    gw_path   : path to the payment_gateway CSV
    bank_path : path to the bank_settlement CSV
    config    : optional configuration; defaults created if None

    Returns
    -------
    ReconciliationResult with matched, partial_matches, exceptions, and
    ingestion_errors lists.
    """
    if config is None:
        config = ReconciliationConfig()

    result = ReconciliationResult(config=config)

    # ------------------------------------------------------------------
    # Stage 1: Ingest
    # ------------------------------------------------------------------
    logger.info("Stage 1: Ingesting CSVs …")
    gw_txs, gw_errors = load_csv(gw_path, source="gateway")
    bank_txs, bank_errors = load_csv(bank_path, source="bank")

    result.ingestion_errors.extend(gw_errors)
    result.ingestion_errors.extend(bank_errors)

    # Ingestion errors surface immediately as exceptions in the report
    for err in result.ingestion_errors:
        result.exceptions.append(_ingestion_error_to_match_result(err))

    # ------------------------------------------------------------------
    # Stage 2: Exact match
    # ------------------------------------------------------------------
    logger.info("Stage 2: Exact matching on reference_number …")
    exact_result = exact_match(gw_txs, bank_txs)
    result.matched.extend(exact_result.matched)

    unmatched_gw: list[Transaction] = exact_result.unmatched_gateway
    unmatched_bank: list[Transaction] = exact_result.unmatched_bank

    # ------------------------------------------------------------------
    # Stage 3: Fuzzy candidate generation
    # ------------------------------------------------------------------
    logger.info("Stage 3: Finding fuzzy candidates …")
    candidates = find_fuzzy_candidates(unmatched_gw, unmatched_bank, config)

    # Track which bank records have been claimed by a fuzzy match
    claimed_bank_ids: set[str] = set()
    claimed_gw_ids: set[str] = set()

    # ------------------------------------------------------------------
    # Stage 4 & 5: LLM reasoning + classification
    # ------------------------------------------------------------------
    logger.info(
        "Stage 4: LLM reasoning for %d fuzzy candidates …",
        len(candidates),
    )
    for pair in candidates:
        if pair.bank_tx.transaction_id in claimed_bank_ids:
            # This bank record was already claimed by a higher-scoring pair
            continue

        llm = reason_match(pair, config)
        match_result = _candidate_to_match_result(pair, llm)

        if match_result.status == MatchStatus.EXCEPTION:
            result.exceptions.append(match_result)
        elif llm.decision == "match":
            result.matched.append(match_result)
        else:
            result.partial_matches.append(match_result)

        claimed_gw_ids.add(pair.gateway_tx.transaction_id)
        claimed_bank_ids.add(pair.bank_tx.transaction_id)

    # ------------------------------------------------------------------
    # Stage 5: True exceptions — records with no match at all
    # ------------------------------------------------------------------
    logger.info("Stage 5: Collecting true exceptions …")

    for tx in unmatched_gw:
        if tx.transaction_id not in claimed_gw_ids:
            result.exceptions.append(_no_match_exception(tx, side="gateway"))

    for tx in unmatched_bank:
        if tx.transaction_id not in claimed_bank_ids:
            result.exceptions.append(_no_match_exception(tx, side="bank"))

    logger.info(
        "Pipeline complete: %d matched, %d partial, %d exceptions (%d ingestion errors).",
        len(result.matched),
        len(result.partial_matches),
        len(result.exceptions),
        len(result.ingestion_errors),
    )
    return result


# ---------------------------------------------------------------------------
# Internal converters
# ---------------------------------------------------------------------------


def _candidate_to_match_result(
    pair: CandidatePair,
    llm_result,
) -> MatchResult:
    """Convert a CandidatePair + LLMResult into a classified MatchResult."""
    if llm_result.available:
        status = (
            MatchStatus.FUZZY_LLM
            if llm_result.decision in ("match", "partial")
            else MatchStatus.EXCEPTION
        )
    else:
        status = (
            MatchStatus.FUZZY_RULE
            if llm_result.decision in ("match", "partial")
            else MatchStatus.EXCEPTION
        )

    return MatchResult(
        gateway_tx=pair.gateway_tx,
        bank_tx=pair.bank_tx,
        status=status,
        confidence=llm_result.confidence,
        rule_score=pair.composite_score,
        discrepancy_notes=pair.discrepancy_notes,
        llm_reasoning=llm_result.reasoning,
        llm_available=llm_result.available,
        matched_at=datetime.datetime.now(),
    )


def _no_match_exception(tx: Transaction, side: str) -> MatchResult:
    """Create an exception MatchResult for a record with no counterpart."""
    return MatchResult(
        gateway_tx=tx if side == "gateway" else None,
        bank_tx=tx if side == "bank" else None,
        status=MatchStatus.EXCEPTION,
        confidence=0.0,
        rule_score=0.0,
        discrepancy_notes=[
            f"No matching record found in {'bank' if side == 'gateway' else 'gateway'} file."
        ],
        llm_reasoning="",
        llm_available=True,
        matched_at=datetime.datetime.now(),
    )


def _ingestion_error_to_match_result(err: IngestionError) -> MatchResult:
    """Wrap an IngestionError as an EXCEPTION MatchResult so it appears in reports."""
    return MatchResult(
        gateway_tx=None,
        bank_tx=None,
        status=MatchStatus.EXCEPTION,
        confidence=0.0,
        rule_score=0.0,
        discrepancy_notes=[
            f"Ingestion error (source={err.source}, row={err.row_index}): {err.reason}"
        ],
        llm_reasoning="",
        llm_available=True,
        matched_at=datetime.datetime.now(),
    )
