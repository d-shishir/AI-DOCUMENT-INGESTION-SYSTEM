import logging
from sqlalchemy.orm import Session
from .models import Lead
from modules.workflow_engine.workflow_manager import workflow_manager

logger = logging.getLogger(__name__)

class LeadService:
    def create_lead(
        self,
        db: Session,
        name: str,
        email: str,
        company: str,
        role: str = None,
        country: str = None,
        source: str = None,
        trigger_workflow: bool = True
    ) -> tuple[Lead, any]:
        """
        Creates a new CRM Lead record and optional triggers onboarding workflow pipeline.
        """
        logger.info(f"Creating lead: {name} ({email}) at {company}")
        
        # Check if email already exists
        existing_lead = db.query(Lead).filter(Lead.email == email).first()
        if existing_lead:
            raise ValueError(f"Lead with email '{email}' already exists.")

        lead = Lead(
            name=name,
            email=email,
            company=company,
            role=role,
            country=country,
            source=source,
            status="new"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        run = None
        if trigger_workflow:
            logger.info(f"Triggering automatic onboarding workflow for lead: {lead.id}")
            try:
                # Dynamically plan/run or run standard onboarding steps
                # We use a standard chain of: enrich_lead -> score_lead -> generate_outreach
                steps = ["enrich_lead", "score_lead", "generate_outreach"]
                
                # Execute the workflow
                run = workflow_manager.executor.execute_workflow(
                    db=db,
                    workflow_name=f"Lead Onboarding - {company}",
                    steps=steps,
                    input_context={"lead_id": str(lead.id)}
                )
                db.refresh(lead)
            except Exception as e:
                logger.error(f"Failed to execute onboarding workflow for lead {lead.id}: {str(e)}")

        return lead, run

    def list_leads(self, db: Session, status: str = None, min_score: int = None) -> list[Lead]:
        query = db.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        if min_score is not None:
            query = query.filter(Lead.lead_score >= min_score)
        return query.order_by(Lead.lead_score.desc()).all()

    def get_lead(self, db: Session, lead_id: str) -> Lead | None:
        return db.query(Lead).filter(Lead.id == lead_id).first()

    def update_lead_status(self, db: Session, lead_id: str, status: str) -> Lead:
        lead = self.get_lead(db, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found.")
        
        lead.status = status
        db.commit()
        db.refresh(lead)
        return lead
