import logging
import json
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

SCORING_SYSTEM_INSTRUCTION = """
You are the AI Lead Scoring Engine for Syntra OS.
Analyze the provided lead details and enrichment profile, and output only valid JSON matching this schema:
{
  "lead_score": 0-100,
  "reasoning": "A brief explanation of how the score was computed based on fit criteria (role seniority, industry relevance, company size)."
}
RULES:
1. Output ONLY a valid JSON object.
2. Fit Criteria:
   - High Seniority (VP, CEO, CTO, Director, Head, Manager): increases score.
   - High Relevance (8-10): increases score.
   - Large Size (Enterprise): increases score.
"""

class ScoringEngine:
    def score_lead(self, lead_data: dict) -> dict:
        """
        Calculates a lead quality score (0-100) and writes fit reasoning.
        """
        logger.info(f"Scoring lead '{lead_data.get('name')}' from company '{lead_data.get('company')}'...")

        if settings.OPENAI_API_KEY:
            try:
                client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE
                )
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": SCORING_SYSTEM_INSTRUCTION},
                        {"role": "user", "content": f"Lead profile dataset:\n{json.dumps(lead_data, indent=2)}"}
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
                logger.error(f"Live scoring LLM call failed: {str(e)}")

        # Fallback Algorithmic Scoring
        return self._calculate_heuristic_score(lead_data)

    def _calculate_heuristic_score(self, lead: dict) -> dict:
        """
        Calculates a fit score (0-100) using static local business rule heuristic.
        """
        score = 50  # Baseline
        reasons = []

        # 1. Seniority Check
        role = str(lead.get("role", "")).lower()
        if any(term in role for term in ["vp", "vice president", "director", "head", "cto", "ceo", "cfo", "chief"]):
            score += 25
            reasons.append("High-level decision maker (executive/VP seniority)")
        elif any(term in role for term in ["manager", "lead", "principal"]):
            score += 15
            reasons.append("Mid-level decision maker (managerial/lead status)")
        else:
            score += 5
            reasons.append("Individual contributor role seniority")

        # 2. Industry Relevance
        rel = int(lead.get("relevance_score") or 5)
        score += (rel * 2.5)  # Max +25
        reasons.append(f"Industry relevance is rated at {rel}/10")

        # 3. Company Size
        size = str(lead.get("estimated_size", "")).lower()
        if "enterprise" in size:
            score += 20
            reasons.append("Enterprise scale organization")
        elif "mid-market" in size:
            score += 10
            reasons.append("Mid-market scale organization")
        else:
            score += 5
            reasons.append("Small business scale organization")

        # Bound score between 0 and 100
        final_score = min(100, max(0, int(score)))
        reasoning_text = "Fit analysis: " + ", ".join(reasons) + "."
        
        return {
            "lead_score": final_score,
            "reasoning": reasoning_text
        }
