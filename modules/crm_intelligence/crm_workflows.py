import logging
from sqlalchemy.orm import Session
from modules.workflow_engine.tool_registry import tool_registry
from .models import Lead
from .enrichment_engine import EnrichmentEngine
from .scoring_engine import ScoringEngine
from .outreach_generator import OutreachGenerator

logger = logging.getLogger(__name__)

# Initialize engine instances
enrichment_engine = EnrichmentEngine()
scoring_engine = ScoringEngine()
outreach_generator = OutreachGenerator()

def enrich_lead_step(db: Session, context: dict, **kwargs):
    """
    Step tool to enrich lead details.
    Requires: lead_id in context or kwargs.
    """
    lead_id = kwargs.get("lead_id") or context.get("lead_id")
    if not lead_id:
        raise ValueError("enrich_lead step requires 'lead_id'")
        
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found in database.")

    enrich_data = enrichment_engine.enrich_lead(db, lead.name, lead.company)
    lead.company_description = enrich_data.get("company_description")
    lead.industry = enrich_data.get("industry")
    lead.estimated_size = enrich_data.get("estimated_size")
    lead.relevance_score = enrich_data.get("relevance_score")
    db.commit()

    return {
        "status": "enriched",
        "industry": lead.industry,
        "relevance_score": lead.relevance_score,
        "estimated_size": lead.estimated_size
    }

def score_lead_step(db: Session, context: dict, **kwargs):
    """
    Step tool to calculate lead fit score.
    Requires: lead_id in context or kwargs.
    """
    lead_id = kwargs.get("lead_id") or context.get("lead_id")
    if not lead_id:
        raise ValueError("score_lead step requires 'lead_id'")
        
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found in database.")

    score_data = scoring_engine.score_lead(lead.to_dict())
    lead.lead_score = score_data.get("lead_score", 0)
    lead.scoring_reasoning = score_data.get("reasoning", "")
    
    # Auto transition lead status based on score thresholds
    if lead.lead_score >= 80:
        lead.status = "qualified"
    elif lead.status == "new":
        lead.status = "contacted"
        
    db.commit()

    return {
        "status": "scored",
        "lead_score": lead.lead_score,
        "scoring_reasoning": lead.scoring_reasoning
    }

def generate_outreach_step(db: Session, context: dict, **kwargs):
    """
    Step tool to generate personalized outreach templates.
    Requires: lead_id in context or kwargs.
    """
    lead_id = kwargs.get("lead_id") or context.get("lead_id")
    if not lead_id:
        raise ValueError("generate_outreach step requires 'lead_id'")
        
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found in database.")

    outreach_templates = outreach_generator.generate_outreach(lead.to_dict())
    lead.outreach_templates = outreach_templates
    db.commit()

    return {
        "status": "outreach_generated",
        "outreach_templates": outreach_templates
    }

# Register tools with central workflow engine
def register_crm_workflow_tools():
    tool_registry.register_tool(
        "enrich_lead",
        enrich_lead_step,
        "Enriches lead company background details using RAG. Input: lead_id."
    )
    tool_registry.register_tool(
        "score_lead",
        score_lead_step,
        "Computes fit qualification score (0-100) for lead data. Input: lead_id."
    )
    tool_registry.register_tool(
        "generate_outreach",
        generate_outreach_step,
        "Generates customized email & connection messages. Input: lead_id."
    )
    logger.info("CRM Intelligence Workflow tools registered successfully.")
