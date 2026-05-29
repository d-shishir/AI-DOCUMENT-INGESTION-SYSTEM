import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from modules.notification_hub.models import Notification
from modules.notification_hub.template_engine import generate_ai_summary
from modules.notification_hub.channel_router import route_notification_channels
from modules.notification_hub.delivery_engine import deliver_to_channels

logger = logging.getLogger(__name__)

def send_notification(db: Session, type: str, priority: str, recipient: str, title: str, payload: dict, module: str = "system") -> Notification:
    """
    Orchestrates the creation, AI summarization, routing, and delivery of a notification.
    """
    # 1. Generate template text (using LLM or fallback)
    message = generate_ai_summary(type, payload)
    
    # 2. Create notification record
    notif = Notification(
        type=type,
        priority=priority,
        recipient=recipient,
        title=title,
        message=message,
        status="pending"
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    
    # 3. Route channels
    channels = route_notification_channels(db, recipient, priority, module)
    
    if not channels:
        logger.info(f"Notification Manager: no delivery channels selected for '{recipient}' due to preferences.")
        notif.status = "sent"
        db.commit()
        return notif
        
    # 4. Deliver
    success = deliver_to_channels(db, notif, channels)
    
    # 5. Update state
    notif.status = "sent" if success else "failed"
    notif.delivered_at = func.now() if success else None
    db.commit()
    
    return notif

# Event Bus listener callbacks
def on_invoice_uploaded_event(event, db: Session):
    send_notification(
        db=db,
        type="invoice_uploaded",
        priority=event.priority,
        recipient="finance_user",
        title="New Invoice Uploaded",
        payload=event.payload or {},
        module="finance"
    )

def on_payroll_processed_event(event, db: Session):
    send_notification(
        db=db,
        type="payroll_processed",
        priority=event.priority,
        recipient="finance_user",
        title="Payroll Batch Dispatched",
        payload=event.payload or {},
        module="finance"
    )

def on_lead_created_event(event, db: Session):
    send_notification(
        db=db,
        type="lead_created",
        priority=event.priority,
        recipient="sales_user",
        title="New CRM Lead Registered",
        payload=event.payload or {},
        module="crm"
    )

def on_workflow_failed_event(event, db: Session):
    send_notification(
        db=db,
        type="workflow_failed",
        priority=event.priority,
        recipient="admin_user",
        title="Workflow Engine Execution Crash",
        payload=event.payload or {},
        module="workflow"
    )

def on_approval_required_event(event, db: Session):
    send_notification(
        db=db,
        type="approval_required",
        priority=event.priority,
        recipient="manager_user",
        title="Gated Operation Verification Required",
        payload=event.payload or {},
        module="system"
    )

def on_anomaly_detected_event(event, db: Session):
    send_notification(
        db=db,
        type="anomaly_alert",
        priority=event.priority,
        recipient="finance_user",
        title="Fintech Compliance Anomaly Flagged",
        payload=event.payload or {},
        module="finance"
    )

def on_security_alert_event(event, db: Session):
    send_notification(
        db=db,
        type="security_alert",
        priority="critical",
        recipient="admin_user",
        title="⚠️ SECURITY POLICY VIOLATION DETECTED",
        payload=event.payload or {},
        module="system"
    )

def subscribe_notification_listeners():
    """
    Binds the notification manager callbacks to the central Event Bus.
    """
    try:
        from modules.event_system.event_registry import event_registry
        event_registry.subscribe("invoice_uploaded", on_invoice_uploaded_event)
        event_registry.subscribe("payroll_processed", on_payroll_processed_event)
        event_registry.subscribe("lead_created", on_lead_created_event)
        event_registry.subscribe("workflow_failed", on_workflow_failed_event)
        event_registry.subscribe("approval_required", on_approval_required_event)
        event_registry.subscribe("anomaly_detected", on_anomaly_detected_event)
        event_registry.subscribe("security_alert", on_security_alert_event)
        logger.info("Notification Manager: successfully subscribed listeners to Event Bus.")
    except Exception as e:
        logger.error(f"Notification Manager: failed to bind Event Bus listeners: {str(e)}")
