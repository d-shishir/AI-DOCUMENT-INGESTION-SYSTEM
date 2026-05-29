import logging
from sqlalchemy.orm import Session
from modules.auth_system.models import SecurityAuditLog

logger = logging.getLogger(__name__)

def log_security_action(db: Session, user_id: str | None, action: str, resource: str, status: str, ip_address: str | None = None) -> SecurityAuditLog:
    """
    Persists a security audit log record. If status is 'denied' or action represents
    a failed security check, publishes a security_alert event to the Event Bus.
    """
    logger.info(f"Security Audit: User '{user_id}' -> Action: {action} on '{resource}' -> Status: {status}")
    
    log_entry = SecurityAuditLog(
        user_id=user_id or "guest",
        action=action,
        resource=resource,
        status=status,
        ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    # Trigger event alert on unauthorized access or critical failure
    if status == "denied" or action in ["failed_access", "suspicious_login", "suspicious_access"]:
        try:
            from modules.event_system.event_bus import publish_event
            publish_event(
                db=db,
                event_type="security_alert",
                source_module="auth_system",
                payload={
                    "user_id": user_id or "guest",
                    "action": action,
                    "resource": resource,
                    "ip_address": ip_address,
                    "reason": f"Access boundary check failed for resource '{resource}' (Action: '{action}')"
                },
                priority="high"
            )
        except Exception as e:
            logger.warning(f"Security Audit: failed to emit alert event: {str(e)}")

    return log_entry
