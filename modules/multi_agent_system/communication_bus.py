import logging
from sqlalchemy.orm import Session
from modules.multi_agent_system.models import AgentLog

logger = logging.getLogger(__name__)

class CommunicationBus:
    def send_message(
        self,
        db: Session,
        workflow_run_id: str,
        sender: str,
        recipient: str,
        message_type: str,
        content: str,
        metadata: dict = None
    ):
        """
        Sends a structured message from sender agent to recipient agent,
        persisting it on the shared communication log bus.
        """
        meta = metadata or {}
        log_entry = AgentLog(
            workflow_run_id=workflow_run_id,
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            message_metadata=meta
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(
            f"[COMM BUS] Run: {workflow_run_id} | {sender} -> {recipient} "
            f"({message_type}): {content[:80]}..."
        )
        
        # Publish event on the Central Event Bus
        try:
            from modules.event_system.event_bus import publish_event
            publish_event(
                db=db,
                event_type="agent_message_sent",
                source_module="multi_agent_system",
                payload={
                    "workflow_run_id": workflow_run_id,
                    "sender": sender,
                    "recipient": recipient,
                    "message_type": message_type,
                    "content": content
                },
                priority="medium"
            )
        except Exception as e:
            logger.warning(f"Could not publish agent_message_sent event: {str(e)}")

        return log_entry

    def get_logs_for_run(self, db: Session, workflow_run_id: str):
        return db.query(AgentLog).filter(
            AgentLog.workflow_run_id == workflow_run_id
        ).order_by(AgentLog.created_at.asc()).all()

# Global bus instance
communication_bus = CommunicationBus()
