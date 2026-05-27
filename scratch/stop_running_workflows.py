import sys
import os

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_path = os.path.join(root_path, "backend")
for path in [root_path, backend_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from app.database import SessionLocal
from modules.workflow_engine.models import WorkflowRun

def stop_workflows():
    db = SessionLocal()
    try:
        stuck_runs = db.query(WorkflowRun).filter(WorkflowRun.status == "running").all()
        print(f"Found {len(stuck_runs)} stuck workflow runs. Updating to 'failed'...")
        for run in stuck_runs:
            run.status = "failed"
            run.error = "Manually terminated or failed due to system restart/invalid transaction state."
        db.commit()
        print("Update completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    stop_workflows()
