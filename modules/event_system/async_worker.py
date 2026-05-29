import time
import traceback
import threading
import logging
from sqlalchemy import func
from app.database import SessionLocal
from modules.event_system.models import EventJob
from modules.event_system.job_queue import fetch_next_job
from modules.event_system.retry_scheduler import schedule_retry

logger = logging.getLogger(__name__)

# Registry of async job handlers
_job_handlers = {}
_worker_threads = []
_stop_event = threading.Event()

def register_job_handler(job_type: str, handler_func):
    """
    Registers a function to handle jobs of a given job_type.
    handler_func signature: handler_func(payload: dict, db_session)
    """
    _job_handlers[job_type] = handler_func
    logger.info(f"Async Worker: registered job handler for type '{job_type}'")

def _execute_job(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(EventJob).filter(EventJob.id == job_id).first()
        if not job:
            return

        job.status = "running"
        job.started_at = func.now()
        db.commit()

        handler = _job_handlers.get(job.job_type)
        if not handler:
            raise ValueError(f"No handler registered for job type: {job.job_type}")

        # Start observability trace
        trace_id = None
        try:
            from modules.observability.trace_manager import trace_manager
            trace_id = trace_manager.start_trace(
                module=f"job_{job.job_type}",
                input_data=str(job.payload),
                db=db
            )
        except Exception as trace_err:
            logger.warning(f"Async Worker: trace initialization skipped: {str(trace_err)}")

        start_time = time.perf_counter()
        logger.info(f"Async Worker: executing job {job.id} (Type: {job.job_type}, Priority: {job.priority})")
        
        # Invoke actual handler logic
        handler(job.payload or {}, db)

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # End trace successfully
        if trace_id:
            try:
                from modules.observability.trace_manager import trace_manager
                trace_manager.end_trace(trace_id, "Completed job execution", "success", db, duration_ms)
            except Exception as trace_err:
                logger.warning(f"Async Worker: trace termination failed: {str(trace_err)}")

        # Mark job as completed
        job = db.query(EventJob).filter(EventJob.id == job_id).first()
        job.status = "completed"
        job.completed_at = func.now()
        db.commit()
        logger.info(f"Async Worker: completed job {job.id}")

        # Record observability metric
        try:
            from modules.observability.models import SystemMetric
            import uuid
            metric = SystemMetric(
                id=uuid.uuid4(),
                metric_name="event_job_completed_count",
                metric_value=1.0,
                module=job.job_type
            )
            db.add(metric)
            db.commit()
        except Exception as m_err:
            logger.warning(f"Async Worker: metrics tracking failed: {str(m_err)}")

    except Exception as e:
        db.rollback()
        err_msg = f"{str(e)}\n\n{traceback.format_exc()}"
        logger.error(f"Async Worker: error processing job {job_id}: {err_msg}")
        
        try:
            job = db.query(EventJob).filter(EventJob.id == job_id).first()
            if job:
                # Track failure metrics
                try:
                    from modules.observability.models import SystemMetric
                    import uuid
                    metric = SystemMetric(
                        id=uuid.uuid4(),
                        metric_name="event_job_failed_count",
                        metric_value=1.0,
                        module=job.job_type
                    )
                    db.add(metric)
                    db.commit()
                except Exception as m_err:
                    logger.warning(f"Async Worker: error metrics tracking failed: {str(m_err)}")
                
                # Truncate error message if it's too long
                schedule_retry(db, job, err_msg)
        except Exception as retry_err:
            logger.exception(f"Async Worker: failed to schedule retry for job {job_id}: {str(retry_err)}")
    finally:
        db.close()

def _worker_loop():
    logger.info("Async Worker loop started.")
    while not _stop_event.is_set():
        db = SessionLocal()
        job = None
        try:
            job = fetch_next_job(db)
        except Exception as e:
            logger.error(f"Async Worker: poll query failed: {str(e)}")
        finally:
            db.close()

        if job:
            _execute_job(job.id)
        else:
            _stop_event.wait(timeout=1.0)
    logger.info("Async Worker loop stopped.")

def start_workers(num_workers: int = 2):
    global _worker_threads
    if any(t.is_alive() for t in _worker_threads):
        logger.warning("Async Worker: threads already running.")
        return

    _stop_event.clear()
    _worker_threads = []
    for i in range(num_workers):
        t = threading.Thread(target=_worker_loop, name=f"SyntraAsyncWorker-{i}", daemon=True)
        t.start()
        _worker_threads.append(t)
    logger.info(f"Async Worker: started {num_workers} daemon worker threads.")

def stop_workers():
    global _worker_threads
    _stop_event.set()
    for t in _worker_threads:
        t.join(timeout=3.0)
    _worker_threads = []
    logger.info("Async Worker: stopped worker threads.")
