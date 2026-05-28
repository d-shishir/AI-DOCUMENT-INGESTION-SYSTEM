import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class AgentWorkflowRun(Base):
    __tablename__ = "agent_workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    goal = Column(Text, nullable=False)
    status = Column(String(50), default="running", index=True)  # running, success, failed
    execution_plan = Column(JSONB, nullable=True, default=list)  # List of decomposed subtasks
    shared_memory = Column(JSONB, nullable=True, default=dict)    # Shared memory context dict
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    logs = relationship("AgentLog", back_populates="workflow_run", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "goal": self.goal,
            "status": self.status,
            "execution_plan": self.execution_plan,
            "shared_memory": self.shared_memory,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(100), nullable=False)
    recipient = Column(String(100), nullable=False)
    message_type = Column(String(50), nullable=False)  # task_assignment, task_result, info_share, system_broadcast
    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, nullable=True, default=dict)  # named message_metadata to avoid conflict with Base.metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workflow_run = relationship("AgentWorkflowRun", back_populates="logs")

    def to_dict(self):
        return {
            "id": str(self.id),
            "workflow_run_id": str(self.workflow_run_id),
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "content": self.content,
            "message_metadata": self.message_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(JSONB, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_name": self.agent_name,
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
