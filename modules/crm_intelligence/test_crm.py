import sys
import os

# Ensure project root and backend are in python path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_path = os.path.join(root_path, "backend")
for path in [root_path, backend_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from app.database import SessionLocal, engine, Base
from modules.crm_intelligence.models import Lead
from modules.crm_intelligence.lead_service import LeadService
from modules.crm_intelligence.crm_workflows import register_crm_workflow_tools
from modules.workflow_engine.models import WorkflowRun, StepExecutionLog

def run_crm_tests():
    print("Initializing CRM Database & registers tools...")
    Base.metadata.create_all(bind=engine)
    register_crm_workflow_tools()
    
    db = SessionLocal()
    lead_service = LeadService()
    
    try:
        email = "clara.oswald@skaro.co.uk"
        # Cleanup existing lead for clean test
        existing = db.query(Lead).filter(Lead.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()

        # 1. Create a lead and trigger the automated workflow
        print("Creating lead and running onboarding workflow...")
        lead, run = lead_service.create_lead(
            db=db,
            name="Clara Oswald",
            email=email,
            company="Skaro Solutions Software Ltd",
            role="Head of Operations",
            country="UK",
            source="LinkedIn Referral",
            trigger_workflow=True
        )
        print(f"Lead created with ID: {lead.id}")
        print(f"Workflow Run ID: {run.id if run else 'None'} | Status: {run.status if run else 'None'}")
        
        # Verify workflow success and model enrichment outputs
        assert run is not None, "Workflow run was not triggered."
        assert run.status == "success", f"Workflow execution failed: {run.error}"
        
        # Reload lead to verify fields populated by workflow steps
        db.refresh(lead)
        print(f"Enriched Industry: {lead.industry}")
        print(f"Enriched Relevance Score: {lead.relevance_score}")
        print(f"Lead Fit Score: {lead.lead_score}")
        print(f"Scoring fit details: {lead.scoring_reasoning}")
        
        assert lead.industry is not None
        assert lead.relevance_score is not None
        assert lead.lead_score > 0
        assert lead.outreach_templates is not None
        assert "email" in lead.outreach_templates
        assert "linkedin" in lead.outreach_templates
        
        print("\n✔ CRM Module Integration Tests Passed Successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_crm_tests()
