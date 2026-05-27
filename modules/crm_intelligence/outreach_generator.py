import logging
import json
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

OUTREACH_SYSTEM_INSTRUCTION = """
You are the AI Sales Copywriter for Syntra OS.
Generate highly personalized, professional outreach templates tailored for the contact based on their role, company, and industry.
Your output must be a valid JSON object matching this schema:
{
  "email": "Subject: ...\\n\\nBody: ...",
  "linkedin": "A short, engaging connection note (max 300 characters)",
  "followup": "Subject: Re: ...\\n\\nBody: ..."
}
Syntra OS capabilities context to reference:
- Structured AI extraction from PDF documents (invoices, payroll, reports).
- Statistical anomaly detection & validation compliance rules.
- Grounded RAG Chat Knowledge Base connected to PostgreSQL.
RULES:
1. Do NOT make the message feel generic. Include references to their company name.
2. Output ONLY a valid JSON object. Do not wrap in markdown code blocks.
"""

class OutreachGenerator:
    def generate_outreach(self, lead_data: dict) -> dict:
        """
        Creates personalized outbound sales email and LinkedIn notes.
        """
        logger.info(f"Generating personalized outreach templates for '{lead_data.get('name')}'...")
        
        if settings.OPENAI_API_KEY:
            try:
                client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE
                )
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": OUTREACH_SYSTEM_INSTRUCTION},
                        {"role": "user", "content": f"Lead profile dataset:\n{json.dumps(lead_data, indent=2)}"}
                    ],
                    temperature=0.7
                )
                res_content = response.choices[0].message.content.strip()
                if res_content.startswith("```"):
                    import re
                    res_content = re.sub(r"^```(?:json)?\n", "", res_content)
                    res_content = re.sub(r"\n```$", "", res_content)
                return json.loads(res_content)
            except Exception as e:
                logger.error(f"Live outreach generator LLM call failed: {str(e)}")

        # Fallback templates
        return self._generate_fallback_outreach(lead_data)

    def _generate_fallback_outreach(self, lead: dict) -> dict:
        name = lead.get("name", "there")
        company = lead.get("company", "your company")
        role = lead.get("role") or "operations leader"
        industry = lead.get("industry") or "the business sector"
        
        subject = f"Streamlining operations at {company}"
        email_body = (
            f"Hi {name},\n\n"
            f"I came across your profile and noticed your role as {role} at {company}. "
            f"Given your focus in {industry}, I thought you might be interested in how we help operations teams "
            f"automate high-volume document ingestion, run statistical anomaly validation, and build vector search archives "
            f"using pgvector.\n\n"
            f"Syntra OS enables companies to automatically extract structured schemas from PDFs, detect compliance discrepancies, "
            f"and query records in a grounded RAG chat interface.\n\n"
            f"Would you be open to a quick 10-minute introduction call next Tuesday?\n\n"
            f"Best regards,\n"
            f"Syntra OS Sales Intelligence team"
        )
        
        linkedin = (
            f"Hi {name}, saw your work as {role} at {company}. I love how you're navigating operational challenges in {industry}. "
            f"Let's connect! I help companies integrate document ingestion and vector search tools."
        )
        
        followup = (
            f"Subject: Re: {subject}\n\n"
            f"Hi {name},\n\n"
            f"Following up on my previous message. I know operational audits and invoice calculations can get tedious at {company}. "
            f"Our platform, Syntra OS, eliminates manual check times by auto-detecting audit anomalies.\n\n"
            f"Let me know if you have 5 minutes for a quick chat this week.\n\n"
            f"Best,\n"
            f"Syntra OS Team"
        )
        
        return {
            "email": f"Subject: {subject}\n\n{email_body}",
            "linkedin": linkedin,
            "followup": followup
        }
