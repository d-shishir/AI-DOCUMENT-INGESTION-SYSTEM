import contextvars
import time
import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from .models import AITrace, TraceStep, ToolCallMetric, RAGQualityMetric

# Context variables for tracing without manual parameter propagation
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)
current_module = contextvars.ContextVar("current_module", default=None)

class TraceSession:
    """
    Context manager to trace execution blocks automatically.
    Sets thread-safe ContextVar properties.
    """
    def __init__(self, module: str, input_data: str, db: Session):
        self.module = module
        self.input_data = input_data
        self.db = db
        self.trace_id = None
        self.start_time = None
        self.token_trace = None
        self.token_module = None

    def __enter__(self):
        self.start_time = time.time()
        trace = AITrace(
            trace_id=uuid.uuid4(),
            module=self.module,
            input_data=str(self.input_data),
            status="running"
        )
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)
        
        self.trace_id = trace.trace_id
        self.token_trace = current_trace_id.set(self.trace_id)
        self.token_module = current_module.set(self.module)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        latency_ms = int((end_time - self.start_time) * 1000)
        
        trace = self.db.query(AITrace).filter(AITrace.trace_id == self.trace_id).first()
        if trace:
            trace.total_latency_ms = latency_ms
            if exc_type:
                trace.status = "failed"
                trace.final_output = f"Exception: {str(exc_val)}"
                
                # Proactively log the error to error tracking table
                from .error_tracker import error_tracker
                import traceback
                error_tracker.capture_error(
                    module=self.module,
                    error_message=str(exc_val),
                    stack_trace=traceback.format_exc(),
                    input_context={"input_data": self.input_data},
                    trace_id=self.trace_id,
                    db=self.db
                )
            else:
                if not trace.final_output:
                    trace.final_output = "Execution completed successfully."
                trace.status = "success"
            self.db.commit()

        if self.token_trace:
            current_trace_id.reset(self.token_trace)
        if self.token_module:
            current_module.reset(self.token_module)

class TraceManager:
    """
    Singleton manager providing helpers for manual logging and tracing.
    """
    @staticmethod
    def get_current_trace_id() -> Optional[uuid.UUID]:
        return current_trace_id.get()

    @staticmethod
    def get_current_module() -> Optional[str]:
        return current_module.get()

    @staticmethod
    def start_trace(module: str, input_data: str, db: Session) -> uuid.UUID:
        trace = AITrace(
            trace_id=uuid.uuid4(),
            module=module,
            input_data=str(input_data),
            status="running"
        )
        db.add(trace)
        db.commit()
        db.refresh(trace)
        return trace.trace_id

    @staticmethod
    def end_trace(trace_id: uuid.UUID, final_output: str, status: str, db: Session, latency_ms: Optional[int] = None):
        trace = db.query(AITrace).filter(AITrace.trace_id == trace_id).first()
        if trace:
            trace.status = status
            trace.final_output = str(final_output)
            if latency_ms is not None:
                trace.total_latency_ms = latency_ms
            db.commit()

    @staticmethod
    def add_step(trace_id: uuid.UUID, step_name: str, status: str, latency_ms: int, metadata: Dict[str, Any], db: Session) -> uuid.UUID:
        step = TraceStep(
            trace_id=trace_id,
            step_name=step_name,
            status=status,
            latency_ms=latency_ms,
            step_metadata=metadata
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step.id

    @staticmethod
    def add_tool_call(trace_id: uuid.UUID, tool_name: str, input_params: Dict[str, Any], output_result: Dict[str, Any], latency_ms: int, status: str, db: Session) -> uuid.UUID:
        metric = ToolCallMetric(
            trace_id=trace_id,
            tool_name=tool_name,
            input_params=input_params,
            output_result=output_result,
            latency_ms=latency_ms,
            status=status
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric.id

    @staticmethod
    def add_rag_metric(
        trace_id: uuid.UUID, 
        query: str, 
        top_k: int, 
        similarity_scores: List[float], 
        context_relevance: float, 
        hallucination_score: float, 
        answer_confidence: float, 
        retrieved_chunks: List[Dict[str, Any]], 
        db: Session
    ) -> uuid.UUID:
        metric = RAGQualityMetric(
            trace_id=trace_id,
            query=query,
            top_k=top_k,
            similarity_scores=similarity_scores,
            context_relevance=context_relevance,
            hallucination_score=hallucination_score,
            answer_confidence=answer_confidence,
            retrieved_chunks=retrieved_chunks
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric.id

trace_manager = TraceManager()
