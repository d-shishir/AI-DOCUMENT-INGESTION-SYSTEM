# CRM Intelligence & AI Sales Automation Module
from .models import Lead
from .router import router
from .crm_workflows import register_crm_workflow_tools

# Auto register workflow steps when module is imported
register_crm_workflow_tools()
