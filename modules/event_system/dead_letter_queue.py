import logging
from sqlalchemy.orm import Session
from modules.event_system.models import EventJob, DeadLetterJob

logger = logging.getLogger(__name__)

def move_to_dlq(db: Session, job: EventJob, error_message: str):
    """
    Moves a job to the dead letter queue database table and updates the original job status.
    """
    logger.warning(f"Dead Letter Queue: moving job {job.id} (Type: {job.job_type}) to DLQ due to: {error_message}")
    
    dlq_item = DeadLetterJob(
        job_id=job.id,
        job_type=job.job_type,
        payload=job.payload,
        priority=job.priority,
        retry_count=job.retry_count,
        error_message=error_message
    )
    db.add(dlq_item)
    
    job.status = "dead_letter"
    job.error_message = error_message
    db.commit()

def retry_dlq_job(db: Session, dlq_id: str) -> EventJob:
    """
    Manually retries a job stored in the Dead Letter Queue.
    Creates a new queued job and removes the DLQ entry.
    """
    import uuid
    try:
        dlq_uuid = uuid.UUID(dlq_id)
    except ValueError:
        raise ValueError(f"Invalid DLQ ID format: {dlq_id}")

    dlq_job = db.query(DeadLetterJob).filter(DeadLetterJob.id == dlq_uuid).first()
    if not dlq_job:
        raise ValueError(f"DLQ job {dlq_id} not found")

    logger.info(f"Dead Letter Queue: manual retry triggered for DLQ item {dlq_id} (Job Type: {dlq_job.job_type})")
    
    # Re-enqueue the job
    from modules.event_system.job_queue import enqueue_job
    new_job = enqueue_job(
        db=db,
        job_type=dlq_job.job_type,
        payload=dlq_job.payload,
        priority=dlq_job.priority,
        max_retries=3
    )

    # Delete DLQ record
    db.delete(dlq_job)
    
    # Clean up original job record if present to avoid pollution
    original_job = db.query(EventJob).filter(EventJob.id == dlq_job.job_id).first()
    if original_job:
        db.delete(original_job)
        
    db.commit()
    return new_job
