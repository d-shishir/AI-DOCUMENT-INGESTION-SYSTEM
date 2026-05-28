import sys
import os

# Ensure workspace root and backend root are in sys.path
dir_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(dir_path, "..", ".."))
backend_path = os.path.abspath(os.path.join(dir_path, "..", "..", "backend"))

if root_path not in sys.path:
    sys.path.insert(0, root_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal
from modules.multi_agent_system.task_coordinator import task_coordinator
from modules.multi_agent_system.agent_registry import agent_registry
from modules.multi_agent_system.communication_bus import communication_bus
from modules.multi_agent_system.memory_manager import memory_manager

def test_multi_agent_system():
    print("🧪 Running Multi-Agent Operations System Tests...")
    db = SessionLocal()
    try:
        # Test 1: Agent Registry
        agents = agent_registry.list_agents()
        assert len(agents) >= 5, "Registry should contain at least 5 default agents"
        print("✔ Registry contains all core specialized agents.")

        # Test 2: Task Decomposition
        goal = "Review uploaded payroll records and identify compliance risks"
        plan = task_coordinator.decompose_goal(goal)
        assert len(plan) > 0, "Plan should contain subtasks"
        print(f"✔ Task decomposition planner succeeded. Steps generated: {len(plan)}")

        # Test 3: Autonomous execution flow
        context = {"query": "standard compliance policy", "limit": 2}
        print("🚀 Executing autonomous task run...")
        res = task_coordinator.run_autonomous_workflow(goal, context, db)
        
        assert res["status"] == "success", "Workflow execution failed"
        run_id = res["run_id"]
        print(f"✔ Autonomous pipeline finished. Workflow Run ID: {run_id}")

        # Test 4: Communication Bus Logging
        logs = communication_bus.get_logs_for_run(db, run_id)
        assert len(logs) > 0, "No communication bus logs were written"
        print(f"✔ Communication Bus successfully captured {len(logs)} message transfers.")

        # Test 5: Shared Memory Validation
        memory = memory_manager.get_short_term_memory(db, run_id)
        assert "research_agent_result" in memory or "research_agent_summary" in memory, "Research agent failed to write to shared memory"
        assert "final_report" in memory, "Final report was not saved to shared memory"
        print("✔ Shared memory context persisted values successfully.")

        print("\n🎉 ALL MULTI-AGENT SYSTEM TESTS PASSED SUCCESSFULLY! 🎉")
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    test_multi_agent_system()
