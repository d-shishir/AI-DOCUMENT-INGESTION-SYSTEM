import sys
import os
import uuid

# Ensure the root of the project and backend are in python path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_path = os.path.join(root_path, "backend")
for path in [root_path, backend_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from app.database import SessionLocal, engine, Base
from app.models import Document
from modules.workflow_engine.models import Workflow, WorkflowRun, StepExecutionLog
from modules.workflow_engine.workflow_executor import WorkflowExecutor
from modules.workflow_engine.workflow_manager import workflow_manager
from modules.workflow_engine.tool_registry import tool_registry

def run_tests():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Create a dummy document to process
        print("Creating mock document...")
        doc = Document(
            id=uuid.uuid4(),
            filename="test_invoice.pdf",
            content="Invoice INV-999\nVendor: Syntra Solutions Ltd\nSubtotal: 1000.00\nTax: 100.00\nTotal: 1100.00\nDue Date: 2026-06-30",
            file_size=150,
            mime_type="application/pdf"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"Mock document created: {doc.id}")

        # 2. Register a mock tool that fails and then succeeds to test retries
        fail_count = 0
        def flakey_tool(db_session, context, **kwargs):
            nonlocal fail_count
            if fail_count < 2:
                fail_count += 1
                raise ValueError("Temporary connection failure (mock)")
            return {"status": "recovered", "attempts": fail_count}
        
        tool_registry.register_tool(
            "flakey_step",
            flakey_tool,
            "A test tool that fails twice before succeeding to verify retry behavior."
        )

        # 3. Create a workflow configuration
        print("Creating test workflow definition...")
        wf = workflow_manager.create_workflow(
            db=db,
            name="Test Audit Chain Workflow",
            steps=["extract_document", "detect_anomalies", "flakey_step", "summarize_document", "generate_report"],
            description="Testing automated tool chain execution and retry behaviors."
        )
        print(f"Workflow definition created: {wf.id}")

        # 4. Execute the workflow
        print("Triggering workflow execution...")
        input_context = {"document_id": str(doc.id)}
        run = workflow_manager.trigger_workflow(db, str(wf.id), input_context)
        print(f"Workflow Run Completed with status: {run.status}")
        
        # Verify run status and metrics
        assert run.status == "success", f"Workflow execution failed: {run.error}"
        
        # Verify step logs and retries
        steps = db.query(StepExecutionLog).filter(StepExecutionLog.workflow_run_id == run.id).order_by(StepExecutionLog.created_at.asc()).all()
        print(f"Total steps executed: {len(steps)}")
        assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
        
        # Check flakey step retries
        flakey_log = next(s for s in steps if s.step_name == "flakey_step")
        print(f"Flakey step retry count: {flakey_log.retry_count}")
        assert flakey_log.retry_count == 2, f"Expected 2 retries, got {flakey_log.retry_count}"
        assert flakey_log.status == "success"
        
        # Check output chaining
        print(f"Chained output context keys: {list(run.output_context.keys())}")
        assert "extracted_data" in run.output_context
        assert "summary" in run.output_context
        assert "report_text" in run.output_context
        
        # 5. Verify Failure Tracking and Partial Recovery Log
        print("Testing a terminal failing step...")
        def terminal_failure_tool(db_session, context, **kwargs):
            raise RuntimeError("Fatal system error")
            
        tool_registry.register_tool(
            "terminal_fail_step",
            terminal_failure_tool,
            "A test tool that fails terminally."
        )
        
        fail_wf = workflow_manager.create_workflow(
            db=db,
            name="Test Failure Workflow",
            steps=["extract_document", "terminal_fail_step", "summarize_document"],
            description="Testing terminal workflow step failure handling."
        )
        
        fail_run = workflow_manager.trigger_workflow(db, str(fail_wf.id), {"document_id": str(doc.id)})
        print(f"Failed Run Completed with status: {fail_run.status}")
        assert fail_run.status == "failed"
        assert "terminal_fail_step" in fail_run.error
        
        # Verify step log for the failure is present
        fail_logs = db.query(StepExecutionLog).filter(StepExecutionLog.workflow_run_id == fail_run.id).all()
        failed_step_log = next(s for s in fail_logs if s.step_name == "terminal_fail_step")
        assert failed_step_log.status == "failed"
        assert "Fatal system error" in failed_step_log.error

        print("\n✔ All tests passed successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
