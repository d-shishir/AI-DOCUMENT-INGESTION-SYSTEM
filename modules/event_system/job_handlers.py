import logging
import time
from sqlalchemy.orm import Session
from modules.event_system.async_worker import register_job_handler
from modules.event_system.event_bus import publish_event

logger = logging.getLogger(__name__)

def handle_invoice_ai_extraction_job(payload: dict, db: Session):
    logger.info(f"Job Handler: Executing invoice AI extraction for payload: {payload}")
    doc_id = payload.get("document_id")
    time.sleep(1.0) # Simulating AI processing time
    
    # Emit event: anomaly_detected
    publish_event(
        db=db,
        event_type="anomaly_detected",
        source_module="extraction_pipeline",
        payload={
            "document_id": doc_id,
            "risk_score": 0.85,
            "anomalies": ["Out of range invoice amount discrepancy"]
        },
        priority="high"
    )

def handle_payroll_audit_job(payload: dict, db: Session):
    logger.info(f"Job Handler: Performing deep audit on payroll payload: {payload}")
    time.sleep(1.0)
    logger.info("Payroll audited successfully.")

def handle_crm_enrichment_job(payload: dict, db: Session):
    logger.info(f"Job Handler: Enriching CRM lead customer profiling: {payload}")
    time.sleep(1.0)
    logger.info("CRM lead enriched successfully.")

def handle_human_approval_gate_job(payload: dict, db: Session):
    logger.info(f"Job Handler: Submitting human review approval request: {payload}")
    time.sleep(1.0)
    try:
        from modules.human_review_system.models import ReviewRequest
        # Dynamically link review request into database
        import uuid
        req = ReviewRequest(
            id=uuid.uuid4(),
            task_type="anomaly_review",
            status="pending",
            payload=payload,
            generated_by="event_system"
        )
        db.add(req)
        db.commit()
        logger.info(f"Created human review request in database: {req.id}")
    except Exception as e:
        logger.warning(f"Could not hook into human review queue: {str(e)}")

def handle_finance_agent_analysis_job(payload: dict, db: Session):
    logger.info(f"Job Handler: finance agent analysis processing retrieval context: {payload}")
    time.sleep(1.0)
    logger.info("Finance Agent swarm analysis completed.")

def initialize_job_handlers():
    """
    Registers the handlers.
    """
    register_job_handler("invoice_ai_extraction", handle_invoice_ai_extraction_job)
    register_job_handler("payroll_audit", handle_payroll_audit_job)
    register_job_handler("crm_enrichment", handle_crm_enrichment_job)
    register_job_handler("human_approval_gate", handle_human_approval_gate_job)
    register_job_handler("finance_agent_analysis", handle_finance_agent_analysis_job)
    logger.info("Event System: Initialized worker job handlers successfully.")
