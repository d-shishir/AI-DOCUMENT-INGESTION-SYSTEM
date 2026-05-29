import logging
from sqlalchemy.orm import Session
from modules.event_system.models import EventRecord
from modules.event_system.event_registry import event_registry

logger = logging.getLogger(__name__)

def dispatch_event(db: Session, event: EventRecord):
    """
    Finds all subscriber callbacks registered for this event type and executes them.
    Each subscriber runs in a safe execution block.
    """
    try:
        from modules.dashboard_aggregator.activity_feed import feed_manager
        payload = event.payload or {}
        msg = f"System event '{event.event_type}' published."
        if isinstance(payload, dict):
            msg = payload.get("message") or payload.get("description") or payload.get("title") or msg
        feed_manager.broadcast({
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "source": event.source_module,
            "message": msg,
            "severity": event.priority if event.priority in ["low", "medium", "high", "critical"] else "medium"
        })
    except Exception as e:
        logger.warning(f"Event Dispatcher: Failed to broadcast event: {str(e)}")
    subscribers = event_registry.get_subscribers(event.event_type)
    if not subscribers:
        logger.info(f"Event Dispatcher: no subscribers registered for event '{event.event_type}'")
        return

    logger.info(f"Event Dispatcher: dispatching event '{event.event_type}' to {len(subscribers)} subscribers")
    
    for callback in subscribers:
        try:
            logger.info(f"Event Dispatcher: invoking callback '{callback.__name__ if hasattr(callback, '__name__') else str(callback)}'")
            callback(event, db)
        except Exception as e:
            logger.error(f"Event Dispatcher: error executing subscriber callback for event '{event.event_type}': {str(e)}", exc_info=True)
            # Log error in observability module
            try:
                from modules.observability.error_tracker import error_tracker
                import traceback
                error_tracker.capture_error(
                    module="event_dispatcher",
                    error_message=f"Callback failed: {str(e)}",
                    stack_trace=traceback.format_exc(),
                    input_context=event.to_dict(),
                    db=db
                )
            except Exception as inner:
                logger.error(f"Event Dispatcher: failed to log dispatcher error in observability: {str(inner)}")
