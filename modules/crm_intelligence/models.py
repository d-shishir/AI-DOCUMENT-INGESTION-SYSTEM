import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    status = Column(String(50), default="new", index=True)  # new | contacted | qualified | converted

    # Enriched fields
    company_description = Column(Text, nullable=True)
    industry = Column(String(255), nullable=True)
    estimated_size = Column(String(100), nullable=True)
    relevance_score = Column(Integer, nullable=True)

    # Scored fields
    lead_score = Column(Integer, default=0, index=True)
    scoring_reasoning = Column(Text, nullable=True)

    # Generated Outreach template data
    outreach_templates = Column(JSONB, nullable=True, default=dict)  # {"email": "...", "linkedin": "..."}

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "role": self.role,
            "country": self.country,
            "source": self.source,
            "status": self.status,
            "company_description": self.company_description,
            "industry": self.industry,
            "estimated_size": self.estimated_size,
            "relevance_score": self.relevance_score,
            "lead_score": self.lead_score,
            "scoring_reasoning": self.scoring_reasoning,
            "outreach_templates": self.outreach_templates,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
