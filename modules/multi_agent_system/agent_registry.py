import logging

logger = logging.getLogger(__name__)

DEFAULT_AGENTS = {
    "coordinator_agent": {
        "name": "Coordinator Agent",
        "role": "Orchestrator & Task Planner",
        "description": "Decomposes complex user goals into sequence of actionable subtasks, delegates them to specialized agents, tracks execution, and summarizes final combined results.",
        "capabilities": ["task_decomposition", "agent_delegation", "result_synthesis"],
        "system_prompt": (
            "You are the central Coordinator Agent of Syntra OS. Your job is to break down "
            "the user's business objective into logical subtasks, assign them to the correct specialized "
            "agents, monitor their progress, and compile the final summary report. "
            "Be precise, organized, and coordinate collaboration efficiently."
        )
    },
    "finance_agent": {
        "name": "Finance Agent",
        "role": "Financial Analyst & Auditor",
        "description": "Reviews invoices, payroll records, audits ledger lines, checks calculations, and identifies compliance anomalies.",
        "capabilities": ["invoice_analysis", "payroll_validation", "anomaly_review", "financial_summarization"],
        "system_prompt": (
            "You are the Finance Agent of Syntra OS. You specialize in analyzing invoices, "
            "verifying payroll distributions, auditing payment terms, and flagging anomalies like "
            "overpayments, tax discrepancies, or compliance risks."
        )
    },
    "crm_agent": {
        "name": "CRM Agent",
        "role": "Sales Intelligence Specialist",
        "description": "Analyzes leads, enriches prospect details from web/retrieved docs, scores prospect fit, and drafts personalized outreach templates.",
        "capabilities": ["lead_analysis", "enrichment", "outreach_generation", "sales_intelligence"],
        "system_prompt": (
            "You are the CRM Agent of Syntra OS. You focus on sales intelligence, prospect enrichment "
            "using text summaries, lead fit qualification scoring, and drafting tailored cold emails/copywriting templates."
        )
    },
    "research_agent": {
        "name": "Research Agent",
        "role": "Compliance & Knowledge Researcher",
        "description": "Performs semantic search over vector database, retrieves documents, summarizes text content, and verifies compliance policies.",
        "capabilities": ["document_retrieval", "rag_search", "compliance_research", "knowledge_summarization"],
        "system_prompt": (
            "You are the Research Agent of Syntra OS. You excel at performing semantic vector search "
            "on ingested documents, retrieving grounded context, and writing factual compliance/policy summaries."
        )
    },
    "workflow_agent": {
        "name": "Workflow Agent",
        "role": "Workflow Execution & Automation Controller",
        "description": "Executes defined automation workflow chains, runs backend worker tasks, triggers notifications, and handles retry/recovery of failed steps.",
        "capabilities": ["execute_workflows", "route_tasks", "monitor_execution", "retry_handling"],
        "system_prompt": (
            "You are the Workflow Agent of Syntra OS. You coordinate background worker execution, "
            "trigger webhook integrations, execute named multi-step workflow chains, and retry failed operations."
        )
    }
}

class AgentRegistry:
    def __init__(self):
        self._agents = {**DEFAULT_AGENTS}

    def register_agent(self, key: str, name: str, role: str, description: str, capabilities: list, system_prompt: str):
        self._agents[key] = {
            "name": name,
            "role": role,
            "description": description,
            "capabilities": capabilities,
            "system_prompt": system_prompt
        }
        logger.info(f"Registered agent '{key}': {name}")

    def get_agent(self, key: str):
        return self._agents.get(key)

    def list_agents(self):
        return [
            {"key": key, **info}
            for key, info in self._agents.items()
        ]

    def find_agents_by_capability(self, capability: str):
        matches = []
        for key, info in self._agents.items():
            if capability in info["capabilities"]:
                matches.append(key)
        return matches

# Global registry instance
agent_registry = AgentRegistry()
