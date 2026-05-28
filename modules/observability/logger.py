import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from .models import StructuredLog
from .trace_manager import trace_manager

# Standard logging handler setup
std_logger = logging.getLogger("SyntraObservability")
if not std_logger.handlers:
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(message)s"))
    std_logger.addHandler(sh)
    std_logger.setLevel(logging.INFO)

class StructuredLogger:
    """
    Custom structured logger routing formatted JSON records to standard console
    and database-backed `StructuredLog` table for live trace querying.
    """
    @staticmethod
    def _log(
        severity: str, 
        message: str, 
        module: Optional[str] = None, 
        trace_id: Optional[Any] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ):
        metadata = metadata or {}
        
        # Autocomplete contextual parameters
        t_id = trace_id or trace_manager.get_current_trace_id()
        m_name = module or trace_manager.get_current_module() or "system"
        
        # Output structured line
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "module": m_name,
            "trace_id": str(t_id) if t_id else None,
            "message": message,
            "metadata": metadata
        }
        std_logger.log(
            getattr(logging, severity, logging.INFO),
            json.dumps(log_entry)
        )
        
        # Write to Database asynchronously/synchronously depending on Session context
        if db:
            try:
                db_log = StructuredLog(
                    trace_id=t_id,
                    module=m_name,
                    severity=severity,
                    message=message,
                    log_metadata=metadata
                )
                db.add(db_log)
                db.commit()
            except Exception as e:
                # Fail gracefully to console
                std_logger.error(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "ERROR",
                    "module": "observability_logger",
                    "message": f"Could not write log to DB: {str(e)}",
                    "metadata": {}
                }))

    def info(self, message: str, module: Optional[str] = None, trace_id: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None, db: Optional[Session] = None):
        self._log("INFO", message, module, trace_id, metadata, db)

    def warning(self, message: str, module: Optional[str] = None, trace_id: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None, db: Optional[Session] = None):
        self._log("WARNING", message, module, trace_id, metadata, db)

    def error(self, message: str, module: Optional[str] = None, trace_id: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None, db: Optional[Session] = None):
        self._log("ERROR", message, module, trace_id, metadata, db)

    def debug(self, message: str, module: Optional[str] = None, trace_id: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None, db: Optional[Session] = None):
        self._log("DEBUG", message, module, trace_id, metadata, db)

logger = StructuredLogger()
