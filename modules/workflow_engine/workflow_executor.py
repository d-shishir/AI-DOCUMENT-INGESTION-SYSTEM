import time
import logging
from sqlalchemy.orm import Session
from .workflow_logger import WorkflowLogger
from .task_router import TaskRouter
from .retry_handler import RetryHandler
from .models import WorkflowRun

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.5):
        self.router = TaskRouter()
        self.retry_handler = RetryHandler(max_retries=max_retries, backoff_factor=backoff_factor)

    def execute_workflow(
        self,
        db: Session,
        workflow_name: str,
        steps: list[str],
        input_context: dict,
        workflow_id: str | None = None
    ) -> WorkflowRun:
        """
        Executes a workflow pipeline step-by-step.
        """
        # 1. Initialize the run log
        run = WorkflowLogger.start_run(db, workflow_name, workflow_id, input_context)
        context = input_context.copy()
        
        logger.info(f"Starting execution of workflow '{workflow_name}' (Run ID: {run.id})")
        
        current_status = "success"
        run_error = None
        
        # Wrapper to rollback database transaction on step failure
        def run_step_with_rollback(db_session, step_name, run_context):
            try:
                # Run the actual tool
                return self.router.route_and_execute(db_session, step_name, run_context)
            except Exception as e:
                logger.warning(f"Step '{step_name}' failed database operation. Rolling back transaction: {str(e)}")
                db_session.rollback()
                raise e

        try:
            for step in steps:
                logger.info(f"Processing step '{step}' in workflow run {run.id}")
                start_time = time.perf_counter()
                
                # Use retry handler to run the step
                result, attempts, err_msg = self.retry_handler.execute_with_retry(
                    step,
                    run_step_with_rollback,
                    db,
                    step,
                    context
                )
                
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                
                if err_msg:
                    # Step failed after all retries
                    logger.error(f"Step '{step}' failed in run {run.id}: {err_msg}")
                    try:
                        WorkflowLogger.log_step(
                            db=db,
                            run_id=str(run.id),
                            step_name=step,
                            status="failed",
                            input_data=context,
                            output_data=None,
                            execution_time_ms=duration_ms,
                            retry_count=attempts,
                            error=err_msg
                        )
                    except Exception as log_err:
                        logger.error(f"Failed to write step log to database: {str(log_err)}")
                        db.rollback()
                        
                    current_status = "failed"
                    run_error = f"Step '{step}' failed: {err_msg}"
                    break
                else:
                    # Step succeeded
                    logger.info(f"Step '{step}' succeeded in run {run.id}")
                    
                    # Merge step output back into context for downstream steps
                    if isinstance(result, dict):
                        context.update(result)
                    
                    try:
                        WorkflowLogger.log_step(
                            db=db,
                            run_id=str(run.id),
                            step_name=step,
                            status="success",
                            input_data=context,
                            output_data=result,
                            execution_time_ms=duration_ms,
                            retry_count=attempts
                        )
                    except Exception as log_err:
                        logger.error(f"Failed to write step log to database: {str(log_err)}")
                        db.rollback()
        except Exception as execution_err:
            logger.exception(f"Unhandled error during workflow execution: {str(execution_err)}")
            db.rollback()
            current_status = "failed"
            run_error = f"Unhandled execution error: {str(execution_err)}"

        # 2. Finalize the run log
        try:
            completed_run = WorkflowLogger.complete_run(db, str(run.id), current_status, context, run_error)
            return completed_run
        except Exception as final_err:
            logger.error(f"Failed to complete workflow run logging: {str(final_err)}")
            db.rollback()
            # Try once more with a rolled-back session to mark as failed
            try:
                run.status = "failed"
                run.error = f"Failed to log completion: {str(final_err)}"
                db.commit()
            except:
                pass
            return run
