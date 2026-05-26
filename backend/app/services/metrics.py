import threading
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from .cache import cache_store

logger = logging.getLogger(__name__)

class MetricsManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._total_queries = 0
        self._total_query_time_ms = 0.0

    def record_query(self, duration_ms: float):
        with self._lock:
            self._total_queries += 1
            self._total_query_time_ms += duration_ms

    def get_metrics(self, db: Session) -> dict:
        doc_count = 0
        chunk_count = 0
        
        try:
            doc_count = db.execute(text("SELECT COUNT(*) FROM documents")).scalar() or 0
            chunk_count = db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar() or 0
        except Exception as e:
            logger.error(f"Failed to fetch counts from database for metrics: {str(e)}")
            
        with self._lock:
            avg_time = (self._total_query_time_ms / self._total_queries) if self._total_queries > 0 else 0.0
            
        return {
            "documents_indexed": int(doc_count),
            "total_chunks": int(chunk_count),
            "avg_query_time_ms": float(round(avg_time, 2)),
            "cache_hit_rate": float(round(cache_store.hit_rate * 100, 2))  # percentage
        }

metrics_tracker = MetricsManager()
