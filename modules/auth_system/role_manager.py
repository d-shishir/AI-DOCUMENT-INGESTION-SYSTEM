import logging

logger = logging.getLogger(__name__)

# Predefined role hierarchies and permission profiles
ROLE_PERMISSIONS = {
    "admin": {
        "modules": ["*"],
        "capabilities": ["*"]
    },
    "finance_manager": {
        "modules": ["finance", "workflow", "system"],
        "capabilities": [
            "payroll_records:read", "payroll_records:write", "payroll_records:approve",
            "invoice_records:read", "invoice_records:write", "invoice_records:approve",
            "workflow:execute", "workflow:approve", "ai_governance:override"
        ]
    },
    "compliance_officer": {
        "modules": ["compliance", "workflow", "observability", "system"],
        "capabilities": [
            "payroll_records:read", "invoice_records:read", "audit_records:read", 
            "audit_records:write", "workflow:execute", "compliance_reviews:approve"
        ]
    },
    "sales_rep": {
        "modules": ["crm", "system"],
        "capabilities": [
            "crm_records:read", "crm_records:write"
        ]
    },
    "operations_manager": {
        "modules": ["workflow", "operations", "system"],
        "capabilities": [
            "workflow:execute", "workflow:approve", "document_ingestion:execute"
        ]
    },
    "reviewer": {
        "modules": ["workflow", "system"],
        "capabilities": [
            "document_records:read", "workflow:execute", "reviews:approve"
        ]
    },
    "analyst": {
        "modules": ["observability", "system"],
        "capabilities": [
            "document_records:read", "metrics:read"
        ]
    }
}

def get_role_permissions(role: str) -> dict:
    return ROLE_PERMISSIONS.get(role, {"modules": [], "capabilities": []})
