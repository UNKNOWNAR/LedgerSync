"""
Data models for the transaction reconciliation pipeline.

All domain objects are defined here as frozen dataclasses so they are
immutable and safe to use across pipeline stages.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Core domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Transaction:
    """A single financial transaction from either the gateway or bank file."""

    transaction_id: str
    amount: float
    date: datetime.date
    merchant_name: str
    reference_number: str
    source: str  # "gateway" | "bank"

    def __str__(self) -> str:
        return (
            f"Transaction({self.transaction_id}, ₹{self.amount:.2f}, "
            f"{self.date}, {self.merchant_name!r}, ref={self.reference_number})"
        )


# ---------------------------------------------------------------------------
# Match classification
# ---------------------------------------------------------------------------


class MatchStatus(str, Enum):
    """Classification of a reconciliation outcome."""

    EXACT = "exact"
    FUZZY_LLM = "fuzzy_llm"       # fuzzy + LLM confirmed
    FUZZY_RULE = "fuzzy_rule"     # fuzzy + LLM unavailable
    EXCEPTION = "exception"        # no match found


# ---------------------------------------------------------------------------
# LLM result container
# ---------------------------------------------------------------------------


@dataclass
class LLMResult:
    """Outcome of an LLM reasoning call for a candidate pair."""

    available: bool
    confidence: float               # 0.0 – 1.0
    decision: str                   # "match" | "partial" | "exception"
    reasoning: str
    raw_response: Optional[str] = None


# ---------------------------------------------------------------------------
# Match result
# ---------------------------------------------------------------------------


@dataclass
class MatchResult:
    """
    Represents the outcome of attempting to match one gateway transaction
    against one bank transaction.
    """

    gateway_tx: Optional[Transaction]
    bank_tx: Optional[Transaction]
    status: MatchStatus
    confidence: float               # 0.0 – 1.0
    discrepancy_notes: list[str] = field(default_factory=list)
    llm_reasoning: str = ""
    llm_available: bool = True
    matched_at: Optional[datetime.datetime] = None
    rule_score: float = 0.0

    def to_dict(self) -> dict:
        """Serialise for JSON / JSONL output."""
        return {
            "gateway_tx": _tx_to_dict(self.gateway_tx),
            "bank_tx": _tx_to_dict(self.bank_tx),
            "status": self.status.value,
            "confidence": round(self.confidence, 4),
            "rule_score": round(self.rule_score, 4),
            "discrepancy_notes": self.discrepancy_notes,
            "llm_reasoning": self.llm_reasoning,
            "llm_available": self.llm_available,
            "matched_at": (
                self.matched_at.isoformat() if self.matched_at else None
            ),
        }


def _tx_to_dict(tx: Optional[Transaction]) -> Optional[dict]:
    if tx is None:
        return None
    return {
        "transaction_id": tx.transaction_id,
        "amount": tx.amount,
        "date": tx.date.isoformat(),
        "merchant_name": tx.merchant_name,
        "reference_number": tx.reference_number,
        "source": tx.source,
    }


# ---------------------------------------------------------------------------
# Ingestion error
# ---------------------------------------------------------------------------


@dataclass
class IngestionError:
    """Represents a row that could not be parsed during CSV ingestion."""

    source: str          # "gateway" | "bank"
    row_index: int
    raw_data: dict
    reason: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "row_index": self.row_index,
            "raw_data": self.raw_data,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Pipeline configuration
# ---------------------------------------------------------------------------


@dataclass
class ReconciliationConfig:
    """
    All tunable thresholds for the reconciliation pipeline.
    All sliders in the Streamlit UI map to fields here.
    """

    # Fuzzy matching thresholds
    date_gap_days: int = 3              # max days apart to consider a fuzzy match
    amount_variance_pct: float = 2.0    # max % amount difference
    merchant_similarity_threshold: float = 80.0  # rapidfuzz score 0–100

    # Weights for composite fuzzy score (must sum to 1.0)
    date_weight: float = 0.30
    amount_weight: float = 0.40
    merchant_weight: float = 0.30

    # Minimum composite score to pass to LLM review (0–1)
    min_candidate_score: float = 0.50

    # LLM settings
    llm_enabled: bool = True
    llm_model: str = "claude-haiku-4-5"
    llm_max_retries: int = 3

    # Output directory
    output_dir: str = "outputs"


# ---------------------------------------------------------------------------
# Top-level pipeline result
# ---------------------------------------------------------------------------


@dataclass
class ReconciliationResult:
    """
    Final output of the reconciliation pipeline.

    matched        – pairs confirmed as the same transaction (exact or LLM-confirmed fuzzy)
    partial_matches – pairs with discrepancies that need review
    exceptions     – records with no match found; includes ingestion errors
    ingestion_errors – rows that failed at the parse stage
    """

    matched: list[MatchResult] = field(default_factory=list)
    partial_matches: list[MatchResult] = field(default_factory=list)
    exceptions: list[MatchResult] = field(default_factory=list)
    ingestion_errors: list[IngestionError] = field(default_factory=list)
    config: Optional[ReconciliationConfig] = None
