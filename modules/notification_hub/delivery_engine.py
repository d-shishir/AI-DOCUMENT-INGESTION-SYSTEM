import time
import logging
from sqlalchemy.orm import Session
from modules.notification_hub.models import Notification, NotificationHistory
from modules.notification_hub.realtime_gateway import broadcast_notification

logger = logging.getLogger(__name__)

def deliver_to_channels(db: Session, notification: Notification, channels: list[str]) -> bool:
    """
    Delivers a notification across one or more target channels.
    Tracks latency and records outcomes in NotificationHistory.
    """
    logger.info(f"Delivery Engine: processing delivery for notification {notification.id} to channels: {channels}")
    
    success = True
    for channel in channels:
        start_time = time.perf_counter()
        channel_success = False
        error_msg = None
        
        try:
            if channel == "in_app":
                channel_success = _deliver_in_app(notification)
            elif channel == "email":
                channel_success = _deliver_email(notification)
            elif channel == "slack":
                channel_success = _deliver_slack(notification)
            elif channel == "sms":
                channel_success = _deliver_sms(notification)
            else:
                raise ValueError(f"Unknown channel: {channel}")
        except Exception as e:
            error_msg = str(e)
            success = False
            logger.error(f"Delivery Engine: failed to deliver over {channel}: {error_msg}")

        latency = int((time.perf_counter() - start_time) * 1000)
        
        # Log to history
        history = NotificationHistory(
            notification_id=notification.id,
            channel=channel,
            status="sent" if channel_success else "failed",
            delivery_latency_ms=latency,
            error_message=error_msg
        )
        db.add(history)
        db.commit()
        
    return success

def _deliver_in_app(notification: Notification) -> bool:
    logger.info(f"[IN-APP ALERT] Recipient: {notification.recipient} | Title: {notification.title} | Message: {notification.message}")
    broadcast_notification(notification.to_dict())
    return True

def _deliver_email(notification: Notification) -> bool:
    logger.info(f"[EMAIL SIMULATION] Sending mail to {notification.recipient}@syntra.io | Subject: {notification.title} | Body: {notification.message}")
    # SMTP/SendGrid mock trigger
    return True

def _deliver_slack(notification: Notification) -> bool:
    logger.info(f"[SLACK SIMULATION] Triggering incoming Webhook | Channel: #ops-alerts | Text: *[{notification.priority.upper()}]* {notification.title}: {notification.message}")
    # Slack Webhook mock trigger
    return True

def _deliver_sms(notification: Notification) -> bool:
    logger.info(f"[SMS SIMULATION] Dispatched text message to Twilio Gateway | To: +1-555-0199 | Message: {notification.title} - {notification.message[:60]}")
    # Twilio SMS mock trigger
    return True
