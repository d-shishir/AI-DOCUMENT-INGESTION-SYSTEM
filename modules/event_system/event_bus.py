import logging
from sqlalchemy.orm import Session
from modules.event_system.models import EventRecord
from modules.observability.trace_manager import trace_manager

logger = logging.getLogger(__name__)

def publish_event(db: Session, event_type: str, source_module: str, payload: dict, priority: str = "medium") -> EventRecord:
    """
    Publishes an event to the system. Saves to the database, extracts trace_id,
    updates observability metrics, and routes to subscribers.
    """
    trace_id = trace_manager.get_current_trace_id()
    trace_id_str = str(trace_id) if trace_id else None

    logger.info(f"Event Bus: publishing event '{event_type}' from '{source_module}' (Priority: {priority}, Trace: {trace_id_str})")

    event_rec = EventRecord(
        event_type=event_type,
        source_module=source_module,
        payload=payload,
        priority=priority,
        trace_id=trace_id_str
    )
    db.add(event_rec)
    db.commit()
    db.refresh(event_rec)

    # Route event through the dispatcher
    from modules.event_system.event_dispatcher import dispatch_event
    try:
        dispatch_event(db, event_rec)
    except Exception as dispatch_err:
        logger.error(f"Event Bus: dispatch failed for event {event_rec.id}: {str(dispatch_err)}")

    # Update system metric
    try:
        from modules.observability.models import SystemMetric
        import uuid
        metric = SystemMetric(
            id=uuid.uuid4(),
            metric_name="event_published_count",
            metric_value=1.0,
            module=source_module
        )
        db.add(metric)
        db.commit()
    except Exception as obs_err:
        logger.warning(f"Event Bus: failed to register observability metric: {str(obs_err)}")

    return event_rec
