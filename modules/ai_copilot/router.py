import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db

from modules.ai_copilot.action_router import handle_copilot_query
from modules.ai_copilot.context_builder import build_system_context

# Attempt to import authentication checks
try:
    from modules.auth_system.access_policies import get_current_user
except ImportError:
    get_current_user = lambda: None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query")
def copilot_query(payload: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Evaluates and executes natural language corporate operations queries.
    """
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required.")
        
    result = handle_copilot_query(query, db, current_user)
    return result

@router.get("/context")
def copilot_context(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Compiles system diagnostics variables.
    """
    return build_system_context(db, current_user)
