import logging
from sqlalchemy.orm import Session
from modules.multi_agent_system.models import AgentWorkflowRun, AgentMemory

logger = logging.getLogger(__name__)

class MemoryManager:
    def get_short_term_memory(self, db: Session, workflow_run_id: str) -> dict:
        """
        Retrieves the shared execution memory context for a specific run.
        """
        run = db.query(AgentWorkflowRun).filter(AgentWorkflowRun.id == workflow_run_id).first()
        if not run:
            return {}
        return run.shared_memory or {}

    def update_short_term_memory(self, db: Session, workflow_run_id: str, key: str, value: any):
        """
        Updates a specific key in the shared execution memory context.
        """
        run = db.query(AgentWorkflowRun).filter(AgentWorkflowRun.id == workflow_run_id).first()
        if not run:
            return
        
        current_memory = dict(run.shared_memory or {})
        current_memory[key] = value
        run.shared_memory = current_memory
        db.commit()
        logger.info(f"[MEMORY] Run {workflow_run_id} | Updated short-term key '{key}'")

    def get_persistent_memory(self, db: Session, agent_name: str, key: str) -> any:
        """
        Retrieves long-term persistent memory for a specific agent.
        """
        mem = db.query(AgentMemory).filter(
            AgentMemory.agent_name == agent_name,
            AgentMemory.key == key
        ).first()
        if not mem:
            return None
        return mem.value

    def update_persistent_memory(self, db: Session, agent_name: str, key: str, value: any):
        """
        Saves or updates long-term persistent memory for a specific agent.
        """
        mem = db.query(AgentMemory).filter(
            AgentMemory.agent_name == agent_name,
            AgentMemory.key == key
        ).first()
        if not mem:
            mem = AgentMemory(
                agent_name=agent_name,
                key=key,
                value=value
            )
            db.add(mem)
        else:
            mem.value = value
        
        db.commit()
        logger.info(f"[MEMORY] Agent {agent_name} | Updated persistent key '{key}'")

# Global memory manager instance
memory_manager = MemoryManager()
