import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class EventRecord(Base):
    __tablename__ = "event_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    source_module = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    payload = Column(JSON, nullable=True)
    priority = Column(String(50), default="medium", nullable=False)  # low, medium, high, critical
    trace_id = Column(String(100), nullable=True, index=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "source_module": self.source_module,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "payload": self.payload,
            "priority": self.priority,
            "trace_id": self.trace_id
        }

class EventJob(Base):
    __tablename__ = "event_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    job_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    status = Column(String(50), default="queued", nullable=False, index=True)  # queued, running, completed, failed, dead_letter
    priority = Column(String(50), default="medium", nullable=False, index=True)  # low, medium, high, critical
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_id": str(self.event_id) if self.event_id else None,
            "job_type": self.job_type,
            "payload": self.payload,
            "status": self.status,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None
        }

class DeadLetterJob(Base):
    __tablename__ = "dead_letter_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    priority = Column(String(50), default="medium", nullable=False)
    retry_count = Column(Integer, default=3, nullable=False)
    error_message = Column(String, nullable=True)
    failed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "job_id": str(self.job_id),
            "job_type": self.job_type,
            "payload": self.payload,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None
        }
