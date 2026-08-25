"""
Reporting layer for the reconciliation pipeline.

Outputs
-------
1. Summary metrics dict
2. matched.csv
3. partial_matches.csv
4. exceptions.csv
5. exception_report.md  — human-readable narrative
6. audit_trail.jsonl    — full decision record per match, timestamped

Public API
----------
generate_summary_metrics(result) -> dict
write_all_reports(result, output_dir)
"""

from __future__ import annotations

import csv
import datetime
import json
import logging
from pathlib import Path
from typing import Optional

from .models import MatchResult, MatchStatus, ReconciliationResult, Transaction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------


def generate_summary_metrics(result: ReconciliationResult) -> dict:
    """
    Compute high-level reconciliation metrics.

    Returns a dict suitable for display in Streamlit metric cards or logging.
    """
    total_gateway = _count_side(result, "gateway")
    total_bank = _count_side(result, "bank")
    total_records = total_gateway + total_bank

    exact_count = sum(
        1 for m in result.matched if m.status == MatchStatus.EXACT
    )
    fuzzy_llm_count = sum(
        1 for m in result.matched if m.status == MatchStatus.FUZZY_LLM
    )
    fuzzy_rule_count = sum(
        1 for m in result.matched if m.status == MatchStatus.FUZZY_RULE
    )
    partial_count = len(result.partial_matches)
    exception_count = len(result.exceptions)
    ingestion_error_count = len(result.ingestion_errors)

    matched_count = len(result.matched)

    # Match rate = confirmed matches / total gateway records
    match_rate_pct = (
        round(matched_count / total_gateway * 100, 2) if total_gateway > 0 else 0.0
    )

    return {
        "total_gateway_records": total_gateway,
        "total_bank_records": total_bank,
        "total_records": total_records,
        "matched_count": matched_count,
        "match_rate_pct": match_rate_pct,
        "exact_matches": exact_count,
        "fuzzy_llm_matches": fuzzy_llm_count,
        "fuzzy_rule_matches": fuzzy_rule_count,
        "partial_matches": partial_count,
        "exceptions": exception_count,
        "ingestion_errors": ingestion_error_count,
    }


# ---------------------------------------------------------------------------
# Write all reports
# ---------------------------------------------------------------------------


def write_all_reports(
    result: ReconciliationResult,
    output_dir: str | Path = "outputs",
) -> dict[str, Path]:
    """
    Write all output files.  Returns a dict mapping report name → Path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}

    paths["matched_csv"] = _write_matched_csv(result, out)
    paths["partial_csv"] = _write_partial_csv(result, out)
    paths["exceptions_csv"] = _write_exceptions_csv(result, out)
    paths["exception_report_md"] = _write_exception_report_md(result, out)
    paths["audit_trail_jsonl"] = _write_audit_trail(result, out)

    logger.info("All reports written to '%s'.", out)
    return paths


# ---------------------------------------------------------------------------
# Individual writers
# ---------------------------------------------------------------------------


def _write_matched_csv(result: ReconciliationResult, out: Path) -> Path:
    path = out / "matched.csv"
    rows = []
    for m in result.matched:
        rows.append(_flatten_match(m))
    _write_csv(path, rows)
    logger.info("Wrote %d matched rows to %s", len(rows), path)
    return path


def _write_partial_csv(result: ReconciliationResult, out: Path) -> Path:
    path = out / "partial_matches.csv"
    rows = []
    for m in result.partial_matches:
        row = _flatten_match(m)
        row["discrepancy_notes"] = " | ".join(m.discrepancy_notes)
        rows.append(row)
    _write_csv(path, rows)
    logger.info("Wrote %d partial match rows to %s", len(rows), path)
    return path


def _write_exceptions_csv(result: ReconciliationResult, out: Path) -> Path:
    path = out / "exceptions.csv"
    rows = []
    for m in result.exceptions:
        row = _flatten_match(m)
        row["reason"] = " | ".join(m.discrepancy_notes)
        row["llm_reasoning"] = m.llm_reasoning
        rows.append(row)
    _write_csv(path, rows)
    logger.info("Wrote %d exception rows to %s", len(rows), path)
    return path


def _write_exception_report_md(
    result: ReconciliationResult, out: Path
) -> Path:
    """Generate a human-readable Markdown exception report."""
    path = out / "exception_report.md"
    metrics = generate_summary_metrics(result)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: list[str] = [
        "# Transaction Reconciliation — Exception Report",
        f"\n_Generated: {now}_\n",
        "## Summary Metrics\n",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Gateway Records | {metrics['total_gateway_records']} |",
        f"| Total Bank Records | {metrics['total_bank_records']} |",
        f"| Matched (Exact) | {metrics['exact_matches']} |",
        f"| Matched (Fuzzy LLM) | {metrics['fuzzy_llm_matches']} |",
        f"| Matched (Fuzzy Rule) | {metrics['fuzzy_rule_matches']} |",
        f"| Partial Matches | {metrics['partial_matches']} |",
        f"| Exceptions | {metrics['exceptions']} |",
        f"| Ingestion Errors | {metrics['ingestion_errors']} |",
        f"| **Match Rate** | **{metrics['match_rate_pct']}%** |",
        "",
    ]

    # ---- Partial matches section ----
    if result.partial_matches:
        lines.append("## Partial Matches (Require Review)\n")
        for i, m in enumerate(result.partial_matches, 1):
            lines.append(f"### {i}. Partial Match — Confidence {m.confidence:.0%}")
            lines.append("")
            lines.append(_tx_table(m))
            if m.discrepancy_notes:
                lines.append("\n**Discrepancies:**")
                for note in m.discrepancy_notes:
                    lines.append(f"- {note}")
            if m.llm_reasoning:
                lines.append(f"\n**LLM Reasoning:** {m.llm_reasoning}")
            if not m.llm_available:
                lines.append(
                    "\n> ⚠️ LLM was unavailable — confidence based on rule-based score only."
                )
            lines.append("")

    # ---- Exceptions section ----
    if result.exceptions:
        lines.append("## Exceptions (No Match Found)\n")
        for i, m in enumerate(result.exceptions, 1):
            tx = m.gateway_tx or m.bank_tx
            source = "gateway" if m.gateway_tx else "bank"
            tx_id = tx.transaction_id if tx else "N/A"
            lines.append(f"### {i}. Exception — {source.title()} TX `{tx_id}`")
            lines.append("")
            if tx:
                lines.append(_single_tx_table(tx))
            if m.discrepancy_notes:
                lines.append("\n**Reason:**")
                for note in m.discrepancy_notes:
                    lines.append(f"- {note}")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Exception report written to %s", path)
    return path


def _write_audit_trail(result: ReconciliationResult, out: Path) -> Path:
    """Write a JSONL audit trail — one JSON object per match decision."""
    path = out / "audit_trail.jsonl"
    all_results = (
        result.matched + result.partial_matches + result.exceptions
    )
    with path.open("w", encoding="utf-8") as fh:
        for match in all_results:
            record = match.to_dict()
            record["audit_timestamp"] = datetime.datetime.now().isoformat()
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Audit trail written to %s (%d entries)", path, len(all_results))
    return path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_side(result: ReconciliationResult, side: str) -> int:
    """Count unique transactions originating from a given side."""
    ids: set[str] = set()
    for m in result.matched + result.partial_matches + result.exceptions:
        tx = m.gateway_tx if side == "gateway" else m.bank_tx
        if tx:
            ids.add(tx.transaction_id)
    return len(ids)


def _flatten_match(m: MatchResult) -> dict:
    def _tx_fields(tx: Optional[Transaction], prefix: str) -> dict:
        if tx is None:
            return {f"{prefix}_{k}": "" for k in ["transaction_id", "amount", "date", "merchant_name", "reference_number"]}
        return {
            f"{prefix}_transaction_id": tx.transaction_id,
            f"{prefix}_amount": tx.amount,
            f"{prefix}_date": tx.date.isoformat(),
            f"{prefix}_merchant_name": tx.merchant_name,
            f"{prefix}_reference_number": tx.reference_number,
        }

    row = {}
    row.update(_tx_fields(m.gateway_tx, "gw"))
    row.update(_tx_fields(m.bank_tx, "bank"))
    row["status"] = m.status.value
    row["confidence"] = round(m.confidence, 4)
    row["rule_score"] = round(m.rule_score, 4)
    row["llm_available"] = m.llm_available
    return row


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _tx_table(m: MatchResult) -> str:
    gw, bank = m.gateway_tx, m.bank_tx
    lines = [
        "| Field | Gateway | Bank |",
        "|---|---|---|",
    ]
    fields = ["transaction_id", "amount", "date", "merchant_name", "reference_number"]
    for f in fields:
        gv = str(getattr(gw, f, "—")) if gw else "—"
        bv = str(getattr(bank, f, "—")) if bank else "—"
        lines.append(f"| {f} | {gv} | {bv} |")
    return "\n".join(lines)


def _single_tx_table(tx: Transaction) -> str:
    lines = [
        "| Field | Value |",
        "|---|---|",
        f"| transaction_id | {tx.transaction_id} |",
        f"| amount | ₹{tx.amount:.2f} |",
        f"| date | {tx.date} |",
        f"| merchant_name | {tx.merchant_name} |",
        f"| reference_number | {tx.reference_number} |",
        f"| source | {tx.source} |",
    ]
    return "\n".join(lines)
