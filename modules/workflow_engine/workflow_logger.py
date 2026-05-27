import logging
from sqlalchemy.orm import Session
from datetime import datetime
from .models import WorkflowRun, StepExecutionLog

logger = logging.getLogger(__name__)

class WorkflowLogger:
    @staticmethod
    def start_run(db: Session, workflow_name: str, workflow_id: str | None, input_context: dict) -> WorkflowRun:
        run = WorkflowRun(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            status="running",
            input_context=input_context,
            output_context={},
            started_at=datetime.utcnow()
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def log_step(
        db: Session,
        run_id: str,
        step_name: str,
        status: str,
        input_data: dict,
        output_data: dict | None,
        execution_time_ms: int,
        retry_count: int,
        error: str | None = None
    ) -> StepExecutionLog:
        step_log = StepExecutionLog(
            workflow_run_id=run_id,
            step_name=step_name,
            status=status,
            input_data=input_data,
            output_data=output_data,
            execution_time_ms=execution_time_ms,
            retry_count=retry_count,
            error=error
        )
        db.add(step_log)
        db.commit()
        db.refresh(step_log)
        return step_log

    @staticmethod
    def complete_run(db: Session, run_id: str, status: str, output_context: dict, error: str | None = None) -> WorkflowRun:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if run:
            run.status = status
            run.output_context = output_context
            run.completed_at = datetime.utcnow()
            run.error = error
            db.commit()
            db.refresh(run)
        return run
