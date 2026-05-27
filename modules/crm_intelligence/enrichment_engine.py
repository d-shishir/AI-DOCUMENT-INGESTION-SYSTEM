import logging
import json
from sqlalchemy.orm import Session
from app.services.rag_pipeline import ask_question_rag
from app.services.embeddings import get_embedding
from app.services.vector_store import search_similar_chunks
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

ENRICHMENT_SYSTEM_INSTRUCTION = """
You are the AI Sales Lead Enrichment Engine for Syntra OS.
Analyze the provided company info and optional RAG context documents, then output only valid JSON matching this schema:
{
  "company_description": "A concise paragraph summarizing the company business profile and operations based on findings.",
  "industry": "Industry category (e.g. Fintech, SaaS, Healthcare, E-commerce, Logistics)",
  "estimated_size": "Estimated employee size (e.g. Small (1-50), Mid-market (51-500), Enterprise (500+))",
  "relevance_score": 1-10 (How relevant this business sector is for an enterprise operations/AI platform like Syntra OS)
}
RULES:
1. Output ONLY a valid JSON object.
2. Do NOT wrap your output in markdown code blocks.
"""

class EnrichmentEngine:
    def enrich_lead(self, db: Session, name: str, company: str) -> dict:
        """
        Enriches lead profile by searching vector DB for company context
        and asking LLM to compile details.
        """
        logger.info(f"Enriching lead {name} at company '{company}'...")
        
        # 1. Search Vector DB for company details (RAG step)
        rag_context = ""
        try:
            # Query vector store for documents matching company name
            query_vector = get_embedding(company)
            chunks = search_similar_chunks(db, query_vector, limit=3)
            if chunks:
                rag_context = "\n".join([f"Source: {c['filename']}\nContent: {c['content']}" for c in chunks])
                logger.info(f"Enriched lead RAG context successfully compiled ({len(chunks)} chunks).")
        except Exception as e:
            logger.warning(f"Failed to query vector DB for lead enrichment: {str(e)}")

        # 2. Query LLM with context
        if settings.OPENAI_API_KEY:
            try:
                client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE
                )
                user_msg = f"Company Name: {company}\nContact: {name}\n\nInternal Document context findings:\n{rag_context or 'No specific internal documents found.'}"
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": ENRICHMENT_SYSTEM_INSTRUCTION},
                        {"role": "user", "content": user_msg}
                    ],
                    temperature=0.0
                )
                res_content = response.choices[0].message.content.strip()
                if res_content.startswith("```"):
                    import re
                    res_content = re.sub(r"^```(?:json)?\n", "", res_content)
                    res_content = re.sub(r"\n```$", "", res_content)
                return json.loads(res_content)
            except Exception as e:
                logger.error(f"Live enrichment LLM call failed: {str(e)}")

        # Fallback Mock Enrichment
        return self._generate_mock_enrichment(company)

    def _generate_mock_enrichment(self, company: str) -> dict:
        """
        Mock database of industries and descriptions for local testing.
        """
        comp_lower = company.lower()
        if "solution" in comp_lower or "software" in comp_lower or "tech" in comp_lower:
            return {
                "company_description": f"{company} is a SaaS and software systems integrator specializing in scalable technology solutions and infrastructure.",
                "industry": "SaaS / Technology",
                "estimated_size": "Mid-market (51-500)",
                "relevance_score": 9
            }
        elif "bank" in comp_lower or "finance" in comp_lower or "pay" in comp_lower:
            return {
                "company_description": f"{company} is a financial services organization focused on commercial transactions, retail accounts, and payroll operations.",
                "industry": "Fintech / Banking",
                "estimated_size": "Enterprise (500+)",
                "relevance_score": 10
            }
        elif "health" in comp_lower or "med" in comp_lower or "care" in comp_lower:
            return {
                "company_description": f"{company} is a healthcare provider system offering clinical research, inpatient diagnostics, and regional medical operations.",
                "industry": "Healthcare",
                "estimated_size": "Enterprise (500+)",
                "relevance_score": 6
            }
        else:
            return {
                "company_description": f"{company} is an operations company managing consumer goods retail, local logistics networks, and commercial services.",
                "industry": "Services / E-commerce",
                "estimated_size": "Small (1-50)",
                "relevance_score": 7
            }
