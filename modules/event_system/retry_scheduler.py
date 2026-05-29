import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from modules.event_system.models import EventJob

logger = logging.getLogger(__name__)

def schedule_retry(db: Session, job: EventJob, error_message: str, base_delay: int = 2, factor: int = 2):
    """
    Increments retry count, calculates exponential backoff delay,
    and updates the job's next_retry_at time or moves it to the DLQ if exhausted.
    """
    job.retry_count += 1
    if job.retry_count > job.max_retries:
        from modules.event_system.dead_letter_queue import move_to_dlq
        move_to_dlq(db, job, error_message)
        return

    # Exponential delay: e.g., retry_count=1 -> 2s, 2 -> 4s, 3 -> 8s
    delay = base_delay * (factor ** (job.retry_count - 1))
    
    # Calculate next retry timestamp
    next_retry = datetime.utcnow() + timedelta(seconds=delay)
    
    logger.info(f"Retry Scheduler: scheduling retry {job.retry_count}/{job.max_retries} for job '{job.job_type}' ({job.id}) in {delay} seconds")
    
    job.status = "queued"
    job.next_retry_at = next_retry
    job.error_message = error_message
    db.commit()
