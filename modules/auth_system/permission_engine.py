import logging
from modules.auth_system.role_manager import get_role_permissions

logger = logging.getLogger(__name__)

def check_permission(user_role: str, user_dept: str, required_resource: str, required_action: str) -> bool:
    """
    Evaluates role capabilities and department isolation boundaries.
    """
    if user_role == "admin":
        return True

    role_rules = get_role_permissions(user_role)
    capabilities = role_rules.get("capabilities", [])
    
    # 1. Check capability match (e.g. 'payroll_records:read')
    target = f"{required_resource}:{required_action}"
    has_cap = (target in capabilities) or ("*" in capabilities)
    
    if not has_cap:
        logger.warning(f"Permission Engine: role '{user_role}' lacks capability '{target}'")
        return False

    # 2. Check department isolation boundary
    resource_dept_map = {
        "payroll_records": "finance",
        "invoice_records": "finance",
        "crm_records": "sales",
        "compliance_reviews": "compliance",
        "audit_records": "compliance"
    }
    
    req_dept = resource_dept_map.get(required_resource)
    if req_dept and user_dept != req_dept:
        logger.warning(f"Permission Engine: department violation. User in '{user_dept}' blocked from resource '{required_resource}' owned by '{req_dept}'")
        return False

    return True

def can_override_ai_governance(user_role: str) -> bool:
    """
    Validates if a role is authorized to override AI systems or retrain workflows.
    """
    return user_role in ["admin", "finance_manager", "compliance_officer"]
