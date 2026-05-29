import logging
from sqlalchemy.orm import Session
from modules.dashboard_aggregator.metrics_aggregator import get_dashboard_metrics, calculate_health_score

logger = logging.getLogger(__name__)

def build_system_context(db: Session, current_user = None) -> dict:
    """
    Assembles current system metrics and active user credentials.
    """
    metrics = get_dashboard_metrics(db)
    health = calculate_health_score(db)
    
    user_info = {
        "role": current_user.role if current_user else "admin",
        "department": current_user.department if current_user else "system",
        "name": current_user.name if current_user else "Admin Director"
    }

    return {
        "user": user_info,
        "metrics": metrics,
        "health": health["health_score"],
        "health_status": health["status"]
    }
