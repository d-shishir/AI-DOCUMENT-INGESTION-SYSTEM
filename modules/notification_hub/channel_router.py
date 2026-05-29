import logging
from sqlalchemy.orm import Session
from modules.notification_hub.preference_manager import should_deliver

logger = logging.getLogger(__name__)

def route_notification_channels(db: Session, recipient: str, priority: str, module: str) -> list[str]:
    """
    Evaluates which channels (in_app, email, slack, sms) should receive the notification
    based on the recipient's configuration policies.
    """
    all_channels = ["in_app", "email", "slack", "sms"]
    selected_channels = []
    
    for channel in all_channels:
        if should_deliver(db, recipient, channel, priority, module):
            selected_channels.append(channel)
            
    logger.info(f"Channel Router: resolved channels {selected_channels} for recipient '{recipient}'")
    return selected_channels
