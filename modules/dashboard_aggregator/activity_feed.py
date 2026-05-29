import logging
import asyncio
from typing import Set, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from modules.event_system.models import EventRecord
from modules.observability.models import SystemErrorLog

logger = logging.getLogger(__name__)

class RealtimeFeedManager:
    def __init__(self):
        self.listeners: Set[asyncio.Queue] = set()

    def add_listener(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.listeners.add(q)
        logger.info(f"Dashboard Aggregator: Added listener queue. Total active: {len(self.listeners)}")
        return q

    def remove_listener(self, q: asyncio.Queue):
        self.listeners.discard(q)
        logger.info(f"Dashboard Aggregator: Removed listener queue. Total active: {len(self.listeners)}")

    def broadcast(self, event_data: dict):
        # Format payload
        formatted = {
            "event_type": event_data.get("event_type", "system_event"),
            "timestamp": event_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "source": event_data.get("source", "system"),
            "message": event_data.get("message", ""),
            "severity": event_data.get("severity", "medium")
        }
        for q in list(self.listeners):
            try:
                q.put_nowait(formatted)
            except Exception as e:
                logger.warning(f"Failed to put event into listener queue: {str(e)}")

feed_manager = RealtimeFeedManager()

def get_historical_activity(db: Session, limit: int = 30) -> List[dict]:
    """
    Retrieves and normalizes past system events from EventRecord and SystemErrorLog.
    """
    try:
        events = db.query(EventRecord).order_by(EventRecord.timestamp.desc()).limit(limit).all()
        errors = db.query(SystemErrorLog).order_by(SystemErrorLog.created_at.desc()).limit(limit).all()
        
        feed = []
        
        for e in events:
            payload = e.payload or {}
            msg = f"System event '{e.event_type}' published."
            if isinstance(payload, dict):
                msg = payload.get("message") or payload.get("description") or payload.get("title") or msg
            
            feed.append({
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat() if e.timestamp else datetime.now(timezone.utc).isoformat(),
                "source": e.source_module,
                "message": msg,
                "severity": e.priority if e.priority in ["low", "medium", "high", "critical"] else "medium"
            })
            
        for err in errors:
            feed.append({
                "event_type": "error_logged",
                "timestamp": err.created_at.isoformat() if err.created_at else datetime.now(timezone.utc).isoformat(),
                "source": err.module,
                "message": f"CRITICAL: {err.error_message}",
                "severity": "critical"
            })
            
        # Sort combined feed by timestamp descending
        feed.sort(key=lambda x: x["timestamp"], reverse=True)
        return feed[:limit]
    except Exception as ex:
        logger.error(f"Failed to retrieve activity history: {str(ex)}")
        return []
