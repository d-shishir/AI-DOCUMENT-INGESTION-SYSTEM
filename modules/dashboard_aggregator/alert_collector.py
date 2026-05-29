import logging
from sqlalchemy.orm import Session
from datetime import datetime

from modules.human_review_system.models import ApprovalRequest
from modules.notification_hub.models import Notification

logger = logging.getLogger(__name__)

def get_unified_inbox(db: Session, limit: int = 50) -> list:
    """
    Combines approval requests and notification alerts into a single unified list.
    """
    try:
        # 1. Fetch pending approvals
        approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").all()
        
        # 2. Fetch high/critical alerts
        notifications = db.query(Notification).filter(
            Notification.priority.in_(["high", "critical"]),
            Notification.status != "failed"
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        unified = []
        
        for app in approvals:
            unified.append({
                "id": str(app.id),
                "type": "approval",
                "title": f"Approval Required: {app.task_type.replace('_', ' ').title()}",
                "message": app.risk_reason or f"Risk Score: {app.risk_score}. Action: {app.recommended_action}",
                "priority": app.risk_level,
                "created_at": app.created_at.isoformat() if app.created_at else None,
                "metadata": {
                    "task_type": app.task_type,
                    "risk_score": app.risk_score,
                    "workflow_run_id": str(app.workflow_run_id) if app.workflow_run_id else None,
                    "assigned_department": app.assigned_department
                }
            })
            
        for notif in notifications:
            unified.append({
                "id": str(notif.id),
                "type": "alert",
                "title": notif.title,
                "message": notif.message,
                "priority": notif.priority,
                "created_at": notif.created_at.isoformat() if notif.created_at else None,
                "metadata": {
                    "alert_type": notif.type,
                    "status": notif.status,
                    "recipient": notif.recipient
                }
            })
            
        # Sort unified list by created_at descending
        # Convert isoformat back to datetime or sort string comparison (since isoformat strings sort alphabetically)
        unified.sort(key=lambda x: x["created_at"] or "", reverse=True)
        
        return unified[:limit]
    except Exception as ex:
        logger.error(f"Failed to compile unified alert inbox: {str(ex)}")
        return []
