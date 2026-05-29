import sys
import os

# Ensure the root of the project is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

import unittest
from app.database import engine, Base, SessionLocal

from modules.dashboard_aggregator.metrics_aggregator import get_dashboard_metrics, calculate_health_score
from modules.dashboard_aggregator.alert_collector import get_unified_inbox
from modules.dashboard_aggregator.router import execute_quick_action
from modules.workflow_engine.models import WorkflowRun
from modules.human_review_system.models import ApprovalRequest
from modules.event_system.models import EventRecord, EventJob

class TestDashboardAggregator(unittest.TestCase):
    def setUp(self):
        # Bind connection and ensure tables are created
        self.db = SessionLocal()
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
        self.db.close()

    def test_metrics_aggregation(self):
        print("\n--- 1. Testing Metrics Aggregator ---")
        # Ensure it resolves without crashing
        metrics = get_dashboard_metrics(self.db)
        self.assertIn("active_workflows", metrics)
        self.assertIn("running_agents", metrics)
        self.assertIn("pending_approvals", metrics)
        self.assertIn("failed_jobs", metrics)
        self.assertIn("crm_leads", metrics)
        self.assertIn("finance_alerts", metrics)
        print("✔ Metrics Aggregator returns correct metrics keys.")

    def test_health_scoring(self):
        print("\n--- 2. Testing Health Score Logic ---")
        health = calculate_health_score(self.db)
        self.assertIn("health_score", health)
        self.assertIn("status", health)
        self.assertTrue(0 <= health["health_score"] <= 100)
        self.assertIn(health["status"], ["healthy", "degraded", "critical"])
        print(f"✔ Health calculation resolved: {health['health_score']}/100 ({health['status']})")

    def test_inbox_collector(self):
        print("\n--- 3. Testing Unified Inbox Aggregation ---")
        inbox = get_unified_inbox(self.db)
        self.assertIsInstance(inbox, list)
        if len(inbox) > 0:
            first_item = inbox[0]
            self.assertIn("id", first_item)
            self.assertIn("type", first_item)
            self.assertIn("title", first_item)
            self.assertIn("priority", first_item)
        print("✔ Alert Collector processes inbox items successfully.")

    def test_quick_action_guards(self):
        print("\n--- 4. Testing Quick Action Permissions ---")
        # Guest mode (no auth) executing search leads (no restrictive role check)
        # Should return success list or handle gracefully
        try:
            res = execute_quick_action(
                action_payload={"action": "search_leads", "parameters": {"query": "non_existent_company"}},
                db=self.db,
                current_user=None # Guest fallback
            )
            self.assertEqual(res["status"], "success")
            print("✔ Guest user query over search actions runs successfully.")
        except Exception as e:
            self.fail(f"Guest lead search failed unexpectedly: {str(e)}")

        # Ops-only trigger workflow without rights should raise HTTPException
        class MockUser:
            role = "sales_rep"
            department = "sales"
            name = "Sales Agent"

        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            execute_quick_action(
                action_payload={"action": "trigger_workflow", "parameters": {"workflow_id": "test"}},
                db=self.db,
                current_user=MockUser()
            )
        self.assertEqual(ctx.exception.status_code, 403)
        print("✔ RBAC capability blocks unauthorized operations triggers.")

if __name__ == "__main__":
    unittest.main()
