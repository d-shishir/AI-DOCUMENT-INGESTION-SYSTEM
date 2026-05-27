import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    steps = Column(JSONB, nullable=False, default=list)  # List of step names or dict configurations
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_name = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", index=True)  # pending, running, success, failed
    input_context = Column(JSONB, nullable=True, default=dict)
    output_context = Column(JSONB, nullable=True, default=dict)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)

    # Relationships
    step_logs = relationship("StepExecutionLog", back_populates="workflow_run", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "input_context": self.input_context,
            "output_context": self.output_context,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }

class StepExecutionLog(Base):
    __tablename__ = "step_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # success, failed
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    execution_time_ms = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="step_logs")

    def to_dict(self):
        return {
            "id": str(self.id),
            "workflow_run_id": str(self.workflow_run_id),
            "step_name": self.step_name,
            "status": self.status,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "execution_time_ms": self.execution_time_ms,
            "retry_count": self.retry_count,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
