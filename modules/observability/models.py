import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class AITrace(Base):
    __tablename__ = "ai_traces"

    trace_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    module = Column(String(100), nullable=False, index=True)  # workflow, agent, rag, crm, finance, auth, document_ingestion
    input_data = Column(Text, nullable=True)
    final_output = Column(Text, nullable=True)
    total_latency_ms = Column(Integer, default=0)
    status = Column(String(50), default="running", index=True)  # running, success, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    steps = relationship("TraceStep", back_populates="trace", cascade="all, delete-orphan")
    rag_metrics = relationship("RAGQualityMetric", back_populates="trace", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCallMetric", back_populates="trace", cascade="all, delete-orphan")
    errors = relationship("SystemErrorLog", back_populates="trace", cascade="all, delete-orphan")
    logs = relationship("StructuredLog", back_populates="trace", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "trace_id": str(self.trace_id),
            "module": self.module,
            "input": self.input_data,
            "final_output": self.final_output,
            "total_latency_ms": self.total_latency_ms,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class TraceStep(Base):
    __tablename__ = "trace_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("ai_traces.trace_id", ondelete="CASCADE"), nullable=False, index=True)
    step_name = Column(String(255), nullable=False)
    status = Column(String(50), default="success")  # success, failed
    latency_ms = Column(Integer, default=0)
    step_metadata = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trace = relationship("AITrace", back_populates="steps")

    def to_dict(self):
        return {
            "id": str(self.id),
            "trace_id": str(self.trace_id),
            "step_name": self.step_name,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "metadata": self.step_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class RAGQualityMetric(Base):
    __tablename__ = "rag_quality_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("ai_traces.trace_id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    top_k = Column(Integer, default=5)
    similarity_scores = Column(JSONB, nullable=True, default=list)  # List of floats
    context_relevance = Column(Float, default=1.0)
    hallucination_score = Column(Float, default=0.0)
    answer_confidence = Column(Float, default=1.0)
    retrieved_chunks = Column(JSONB, nullable=True, default=list)  # List of dicts: chunk_id, content, doc_id
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trace = relationship("AITrace", back_populates="rag_metrics")

    def to_dict(self):
        return {
            "id": str(self.id),
            "trace_id": str(self.trace_id),
            "query": self.query,
            "top_k": self.top_k,
            "similarity_scores": self.similarity_scores,
            "context_relevance": self.context_relevance,
            "hallucination_score": self.hallucination_score,
            "answer_confidence": self.answer_confidence,
            "retrieved_chunks": self.retrieved_chunks,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ToolCallMetric(Base):
    __tablename__ = "tool_call_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("ai_traces.trace_id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    input_params = Column(JSONB, nullable=True, default=dict)
    output_result = Column(JSONB, nullable=True, default=dict)
    latency_ms = Column(Integer, default=0)
    status = Column(String(50), default="success")  # success, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trace = relationship("AITrace", back_populates="tool_calls")

    def to_dict(self):
        return {
            "id": str(self.id),
            "trace_id": str(self.trace_id),
            "tool_name": self.tool_name,
            "input": self.input_params,
            "output": self.output_result,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class SystemErrorLog(Base):
    __tablename__ = "system_error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("ai_traces.trace_id", ondelete="SET NULL"), nullable=True, index=True)
    module = Column(String(100), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    input_context = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    trace = relationship("AITrace", back_populates="errors")

    def to_dict(self):
        return {
            "id": str(self.id),
            "trace_id": str(self.trace_id) if self.trace_id else None,
            "module": self.module,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "input_context": self.input_context,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class SystemMetric(Base):
    __tablename__ = "observability_system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    metric_name = Column(String(100), nullable=False, index=True)  # request_count, avg_latency, token_usage, error_count, etc.
    metric_value = Column(Float, nullable=False)
    module = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "module": self.module,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class StructuredLog(Base):
    __tablename__ = "structured_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("ai_traces.trace_id", ondelete="SET NULL"), nullable=True, index=True)
    module = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), default="INFO", index=True)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    log_metadata = Column(JSONB, nullable=True, default=dict)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    trace = relationship("AITrace", back_populates="logs")

    def to_dict(self):
        return {
            "id": str(self.id),
            "trace_id": str(self.trace_id) if self.trace_id else None,
            "module": self.module,
            "severity": self.severity,
            "message": self.message,
            "metadata": self.log_metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
