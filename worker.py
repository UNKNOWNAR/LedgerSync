import os
import json
import logging
from pathlib import Path
from celery import Celery
from reconciler.models import ReconciliationConfig
from reconciler.pipeline import run_pipeline
from reconciler.reporting import write_all_reports, generate_summary_metrics

logger = logging.getLogger(__name__)

# Configure Celery to use Redis as the broker and backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "finance_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

@celery_app.task(bind=True, name="reconcile_job")
def reconcile_job(self, gw_path_str: str, bank_path_str: str, config_dict: dict, out_dir_str: str):
    logger.info(f"Starting reconciliation job {self.request.id}")
    try:
        gw_path = Path(gw_path_str)
        bank_path = Path(bank_path_str)
        out_dir = Path(out_dir_str)
        
        config = ReconciliationConfig(**config_dict)
        
        # Update state to PROCESSING
        self.update_state(state="PROCESSING", meta={"status": "Running pipeline"})
        
        result = run_pipeline(gw_path, bank_path, config)
        report_paths = write_all_reports(result, out_dir)
        metrics = generate_summary_metrics(result)
        
        def _serialize_matches(matches):
            return [m.to_dict() for m in matches]
            
        final_result = {
            "run_id": self.request.id,
            "metrics": metrics,
            "matched": _serialize_matches(result.matched),
            "partial_matches": _serialize_matches(result.partial_matches),
            "exceptions": _serialize_matches(result.exceptions),
            "ingestion_errors": [e.to_dict() for e in result.ingestion_errors],
            "report_paths": {k: str(v) for k, v in report_paths.items()}
        }
        
        return final_result
    except Exception as exc:
        logger.exception("Pipeline failed in Celery worker")
        raise exc

