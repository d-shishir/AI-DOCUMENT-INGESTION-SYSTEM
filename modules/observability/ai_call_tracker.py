from sqlalchemy.orm import Session
from .models import SystemMetric
from .trace_manager import trace_manager

class AICallTracker:
    """
    Tracks LLM request token usages, recording metadata and prompt parameters.
    """
    @staticmethod
    def record_token_usage(tokens: int, module: str, db: Session):
        try:
            metric = SystemMetric(
                metric_name="token_usage",
                metric_value=float(tokens),
                module=module
            )
            db.add(metric)
            db.commit()
        except Exception:
            pass

ai_call_tracker = AICallTracker()
