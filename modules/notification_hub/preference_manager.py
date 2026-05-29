import logging
from sqlalchemy.orm import Session
from modules.notification_hub.models import UserNotificationPreference

logger = logging.getLogger(__name__)

def get_preferences(db: Session, recipient: str) -> UserNotificationPreference:
    """
    Retrieves notification preferences for a recipient. 
    If not found, returns a default set of preferences.
    """
    pref = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.recipient == recipient
    ).first()
    
    if not pref:
        # Default configuration
        pref = UserNotificationPreference(
            recipient=recipient,
            in_app_enabled=True,
            email_enabled=False,
            slack_enabled=False,
            sms_enabled=False,
            severity_filter="low",
            subscribed_modules=["finance", "crm", "workflow", "system"]
        )
    return pref

def save_preferences(db: Session, recipient: str, data: dict) -> UserNotificationPreference:
    """
    Saves or updates notification preferences for a recipient.
    """
    pref = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.recipient == recipient
    ).first()
    
    if not pref:
        pref = UserNotificationPreference(recipient=recipient)
        db.add(pref)

    pref.in_app_enabled = data.get("in_app_enabled", True)
    pref.email_enabled = data.get("email_enabled", False)
    pref.slack_enabled = data.get("slack_enabled", False)
    pref.sms_enabled = data.get("sms_enabled", False)
    pref.severity_filter = data.get("severity_filter", "low")
    pref.subscribed_modules = data.get("subscribed_modules", ["finance", "crm", "workflow", "system"])
    
    db.commit()
    db.refresh(pref)
    return pref

def should_deliver(db: Session, recipient: str, channel: str, priority: str, module: str) -> bool:
    """
    Checks if a notification should be delivered to a recipient based on their preferences.
    """
    pref = get_preferences(db, recipient)
    
    # Check channel enablement
    if channel == "in_app" and not pref.in_app_enabled:
        return False
    if channel == "email" and not pref.email_enabled:
        return False
    if channel == "slack" and not pref.slack_enabled:
        return False
    if channel == "sms" and not pref.sms_enabled:
        return False

    # Check priority filters
    severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    pref_weight = severity_weights.get(pref.severity_filter.lower(), 1)
    notif_weight = severity_weights.get(priority.lower(), 2)
    
    if notif_weight < pref_weight:
        logger.info(f"Preference Manager: skipping delivery to '{recipient}' due to severity filter ({priority} < {pref.severity_filter})")
        return False

    # Check module subscriptions
    subscribed = pref.subscribed_modules or []
    if module not in subscribed and "all" not in subscribed:
        logger.info(f"Preference Manager: skipping delivery to '{recipient}' due to module subscription (Module: {module} not in {subscribed})")
        return False

    return True
