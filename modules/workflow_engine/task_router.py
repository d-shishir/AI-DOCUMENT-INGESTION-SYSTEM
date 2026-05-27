import logging
from sqlalchemy.orm import Session
from .tool_registry import tool_registry

logger = logging.getLogger(__name__)

class TaskRouter:
    # Maps user-friendly step names to registered tool names
    STEP_TO_TOOL_MAP = {
        "extract_invoice": "extract_document",
        "extract_document": "extract_document",
        "validate_invoice": "detect_anomalies",
        "detect_anomalies": "detect_anomalies",
        "search_vector_db": "search_vector_db",
        "retrieve_context": "search_vector_db",
        "summarize_document": "summarize_document",
        "send_email": "send_email",
        "notify_team": "send_email",
        "generate_report": "generate_report",
        "store_results": "generate_report"
    }

    def route_and_execute(self, db: Session, step_name: str, context: dict) -> dict:
        """
        Determines the appropriate tool for a step name, prepares parameters from context,
        and runs the tool.
        """
        tool_name = self.STEP_TO_TOOL_MAP.get(step_name, step_name)
        tool = tool_registry.get_tool(tool_name)
        
        if not tool:
            raise ValueError(f"Step '{step_name}' could not be routed. Tool '{tool_name}' not found.")
        
        # Prepare execution arguments by pulling relevant keys from context
        kwargs = {}
        if tool_name == "extract_document":
            kwargs["document_id"] = context.get("document_id")
        elif tool_name == "search_vector_db":
            kwargs["query"] = context.get("query") or context.get("search_query")
            kwargs["limit"] = context.get("limit", 5)
        elif tool_name == "summarize_document":
            kwargs["document_id"] = context.get("document_id")
        elif tool_name == "detect_anomalies":
            kwargs["document_id"] = context.get("document_id")
        elif tool_name == "send_email":
            kwargs["recipient"] = context.get("recipient") or "team@syntra.os"
            # Format custom subject/body if they exist, or use findings from context
            kwargs["subject"] = context.get("subject") or f"Syntra OS Workflow Alert: {step_name}"
            kwargs["body"] = context.get("body") or f"Execution context details: {str(context.get('summary') or context.get('extracted_data') or 'completed successfully')}"
        elif tool_name == "generate_report":
            # Extract content from previous outputs if present
            findings = context.get("summary") or context.get("anomalies") or context.get("extracted_data") or "No recent step findings."
            kwargs["content"] = str(findings)
            kwargs["title"] = context.get("report_title") or "Syntra OS Workflow Run Summary Report"
            
        # Execute the tool
        result = tool_registry.execute_tool(tool_name, db, context, **kwargs)
        return result
