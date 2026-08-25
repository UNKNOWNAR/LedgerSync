"""
FastAPI backend for the Transaction Reconciliation Tool.

Wraps the existing reconciler package with a thin HTTP API.
"""

from __future__ import annotations

import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from reconciler.models import ReconciliationConfig
from reconciler.pipeline import run_pipeline
from reconciler.reporting import generate_summary_metrics, write_all_reports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Transaction Reconciliation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_runs: dict[str, dict[str, Path]] = {}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/reconcile")
async def reconcile(
    gateway_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
    config: str = Form("{}"),
):
    cfg_data = json.loads(config)
    recon_config = ReconciliationConfig(
        date_gap_days=cfg_data.get("date_gap_days", 3),
        amount_variance_pct=cfg_data.get("amount_variance_pct", 2.0),
        merchant_similarity_threshold=float(cfg_data.get("merchant_similarity_threshold", 80)),
        min_candidate_score=0.50,
        llm_enabled=cfg_data.get("llm_enabled", False),
    )

    tmp = Path(tempfile.mkdtemp())
    gw_path = tmp / "payment_gateway.csv"
    bank_path = tmp / "bank_settlement.csv"
    gw_path.write_bytes(await gateway_file.read())
    bank_path.write_bytes(await bank_file.read())

    try:
        result = run_pipeline(gw_path, bank_path, recon_config)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:
        logger.exception("Pipeline error")
        return JSONResponse(status_code=500, content={"error": str(exc)})

    out_dir = tmp / "outputs"
    report_paths = write_all_reports(result, out_dir)
    metrics = generate_summary_metrics(result)

    run_id = uuid.uuid4().hex[:12]
    _runs[run_id] = report_paths

    def _serialize_matches(matches: list) -> list[dict[str, Any]]:
        rows = []
        for m in matches:
            rows.append(m.to_dict())
        return rows

    return {
        "run_id": run_id,
        "metrics": metrics,
        "matched": _serialize_matches(result.matched),
        "partial_matches": _serialize_matches(result.partial_matches),
        "exceptions": _serialize_matches(result.exceptions),
        "ingestion_errors": [e.to_dict() for e in result.ingestion_errors],
    }


@app.get("/api/reports/{run_id}/{report_name}")
def download_report(run_id: str, report_name: str):
    report_paths = _runs.get(run_id)
    if not report_paths:
        return JSONResponse(status_code=404, content={"error": "Run not found"})

    path = report_paths.get(report_name)
    if not path or not path.exists():
        return JSONResponse(status_code=404, content={"error": "Report not found"})

    media_types = {
        "exceptions_csv": "text/csv",
        "matched_csv": "text/csv",
        "partial_csv": "text/csv",
        "exception_report_md": "text/markdown",
        "audit_trail_jsonl": "application/jsonl",
    }

    return FileResponse(
        path,
        media_type=media_types.get(report_name, "application/octet-stream"),
        filename=path.name,
    )
