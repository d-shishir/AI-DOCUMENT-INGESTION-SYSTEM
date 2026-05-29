import logging
from sqlalchemy.orm import Session
from modules.notification_hub.models import Notification

logger = logging.getLogger(__name__)

def escalate_notification(db: Session, notification_id: str) -> Notification:
    """
    Escalates an unresolved notification. Increases severity priority to 'critical',
    promotes the recipient to executive role, and re-triggers delivery alerts.
    """
    import uuid
    try:
        notif_uuid = uuid.UUID(notification_id)
    except ValueError:
        raise ValueError(f"Invalid notification ID: {notification_id}")

    notif = db.query(Notification).filter(Notification.id == notif_uuid).first()
    if not notif:
        raise ValueError(f"Notification not found: {notification_id}")

    logger.warning(f"Escalation Notifier: Escalating notification {notif.id} (Original Recipient: {notif.recipient})")
    
    # Update properties
    notif.status = "escalated"
    notif.priority = "critical"
    notif.title = f"[ESCALATED] {notif.title}"
    notif.recipient = "ops_director"  # Escalate to director level
    
    db.commit()
    
    # Re-route and deliver to escalated user
    from modules.notification_hub.channel_router import route_notification_channels
    from modules.notification_hub.delivery_engine import deliver_to_channels
    
    channels = route_notification_channels(db, notif.recipient, notif.priority, "system")
    deliver_to_channels(db, notif, channels)
    
    return notif
