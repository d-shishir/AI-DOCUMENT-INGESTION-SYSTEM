import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(String(100), nullable=False, index=True) # workflow_update, approval_request, anomaly_alert, crm_lead, failed_job, compliance_warning, system_health
    priority = Column(String(50), default="medium", nullable=False, index=True) # low, medium, high, critical
    recipient = Column(String(100), nullable=False, index=True) # e.g. finance_user, sales_user, admin
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True) # pending, sent, failed, escalated
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "priority": self.priority,
            "recipient": self.recipient,
            "title": self.title,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None
        }

class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    recipient = Column(String(100), unique=True, nullable=False, index=True) # user_id
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=False, nullable=False)
    slack_enabled = Column(Boolean, default=False, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    severity_filter = Column(String(50), default="low", nullable=False) # low, medium, high, critical (minimum level to notify)
    subscribed_modules = Column(JSON, nullable=True) # e.g. ["finance", "crm", "workflow"]

    def to_dict(self):
        return {
            "id": str(self.id),
            "recipient": self.recipient,
            "in_app_enabled": self.in_app_enabled,
            "email_enabled": self.email_enabled,
            "slack_enabled": self.slack_enabled,
            "sms_enabled": self.sms_enabled,
            "severity_filter": self.severity_filter,
            "subscribed_modules": self.subscribed_modules or []
        }

class NotificationHistory(Base):
    __tablename__ = "notification_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    notification_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel = Column(String(50), nullable=False) # in_app, email, slack, sms
    status = Column(String(50), nullable=False) # sent, failed
    delivery_latency_ms = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "notification_id": str(self.notification_id),
            "channel": self.channel,
            "status": self.status,
            "delivery_latency_ms": self.delivery_latency_ms,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None
        }
