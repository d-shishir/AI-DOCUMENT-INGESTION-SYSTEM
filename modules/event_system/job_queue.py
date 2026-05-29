import logging
from sqlalchemy import case, and_, or_, func
from sqlalchemy.orm import Session
from modules.event_system.models import EventJob

logger = logging.getLogger(__name__)

# Priority priority mapping
PRIORITY_ORDER = case(
    (EventJob.priority == "critical", 1),
    (EventJob.priority == "high", 2),
    (EventJob.priority == "medium", 3),
    (EventJob.priority == "low", 4),
    else_=5
)

def enqueue_job(db: Session, job_type: str, payload: dict, priority: str = "medium", event_id=None, max_retries: int = 3) -> EventJob:
    """
    Enqueues a new background job with a specified priority.
    """
    logger.info(f"Job Queue: enqueueing job '{job_type}' (Priority: {priority}, Max Retries: {max_retries})")
    
    job = EventJob(
        job_type=job_type,
        payload=payload,
        status="queued",
        priority=priority,
        event_id=event_id,
        max_retries=max_retries,
        retry_count=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def fetch_next_job(db: Session) -> EventJob:
    """
    Retrieves the oldest queued job matching the highest priority level.
    Uses 'SELECT FOR UPDATE SKIP LOCKED' if available in Postgres to avoid race conditions.
    Only fetches jobs where next_retry_at is None or in the past.
    """
    now = func.now()
    filter_cond = and_(
        EventJob.status == "queued",
        or_(
            EventJob.next_retry_at == None,
            EventJob.next_retry_at <= now
        )
    )
    
    # Try Postgres skip locked to prevent multiple workers grabbing the same job
    try:
        job = db.query(EventJob).filter(filter_cond).order_by(
            PRIORITY_ORDER.asc(),
            EventJob.created_at.asc()
        ).with_for_update(skip_locked=True).first()
    except Exception:
        # Fallback for SQLite during testing or if DB doesn't support SELECT FOR UPDATE SKIP LOCKED
        db.rollback()
        job = db.query(EventJob).filter(filter_cond).order_by(
            PRIORITY_ORDER.asc(),
            EventJob.created_at.asc()
        ).first()

    return job
