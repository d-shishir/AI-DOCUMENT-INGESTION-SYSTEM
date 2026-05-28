import logging
from modules.multi_agent_system.agent_registry import agent_registry

logger = logging.getLogger(__name__)

class DelegationEngine:
    def delegate_task(self, capability: str) -> str:
        """
        Finds the correct agent for the given capability.
        Falls back to coordinator_agent if no agent matches.
        """
        matching_agents = agent_registry.find_agents_by_capability(capability)
        if not matching_agents:
            # Map common keywords/synonyms to capabilities
            fallback_map = {
                "rag": "research_agent",
                "search": "research_agent",
                "retrieve": "research_agent",
                "invoice": "finance_agent",
                "payroll": "finance_agent",
                "finance": "finance_agent",
                "audit": "finance_agent",
                "lead": "crm_agent",
                "crm": "crm_agent",
                "outreach": "crm_agent",
                "workflow": "workflow_agent",
                "execute": "workflow_agent",
            }
            for kw, agent in fallback_map.items():
                if kw in capability.lower():
                    logger.info(f"[DELEGATE] Found keyword fallback match for '{capability}' -> {agent}")
                    return agent
            
            logger.warning(f"[DELEGATE] No agent found for capability '{capability}'. Defaulting to coordinator_agent.")
            return "coordinator_agent"
            
        # If multiple agents have the capability, return the first one
        logger.info(f"[DELEGATE] Matched capability '{capability}' -> {matching_agents[0]}")
        return matching_agents[0]

# Global delegation engine instance
delegation_engine = DelegationEngine()
