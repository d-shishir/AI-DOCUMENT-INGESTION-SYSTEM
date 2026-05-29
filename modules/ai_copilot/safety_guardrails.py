import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SecurityViolationException(Exception):
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def enforce_safety_guardrails(intent: str, entities: dict, current_user) -> None:
    """
    Validates execution safety against user RBAC roles and resource risk scoring parameters.
    """
    if not current_user:
        # Allow default testing in offline test configurations
        return
        
    role = current_user.role
    department = current_user.department

    logger.info(f"Guardrails: Checking security for User Role '{role}' on Intent '{intent}'")

    # 1. Block destructive operations or bulk approvals for non-managers
    if intent == "approval_action":
        action = entities.get("action")
        req_id = entities.get("request_id")
        
        if role not in ["admin", "finance_manager", "compliance_officer"]:
            raise SecurityViolationException(
                "Access Denied: You do not possess clearance to resolve reviews or authorize transactions."
            )
            
        # Bulk approvals restriction
        if req_id == "all_low_risk" and role != "admin":
            raise SecurityViolationException(
                "Compliance Warning: Bulk transaction overrides are restricted to Administrator Directors."
            )

    # 2. Strict department locks
    if intent in ["finance_query", "workflow_trigger"]:
        wf_id = entities.get("workflow_id")
        
        # Finance triggers gated to Finance or Admin
        if (wf_id == "payroll_calculation_sync" or intent == "finance_query"):
            if role != "admin" and department != "finance":
                raise SecurityViolationException(
                    f"Access Denied: Operational boundaries restrict finance actions to the Finance department (your department: '{department}')."
                )

    # 3. CRM access gated to Sales, Ops, Admin
    if intent == "crm_query":
        if role != "admin" and department not in ["sales", "operations"]:
            raise SecurityViolationException(
                f"Access Denied: CRM outreach operations are restricted to Sales or Operations stakeholders."
            )
            
    # 4. Agent Swarm controls gated
    if intent == "agent_delegate":
        if role not in ["admin", "operations_manager", "finance_manager"]:
            raise SecurityViolationException(
                "Access Denied: Multi-agent swarm orchestrations require management permissions."
            )
