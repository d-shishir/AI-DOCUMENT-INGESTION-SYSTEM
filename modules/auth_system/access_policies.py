import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from modules.auth_system.models import User
from modules.auth_system.jwt_service import verify_token
from modules.auth_system.permission_engine import check_permission
from modules.auth_system.audit_security import log_security_action

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that decodes the access token from Authorization header.
    Raises 401 Unauthorized if credentials fail checks.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required."
        )
        
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing user identity fields."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user account not found."
        )

    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been suspended."
        )

    return user

class PermissionGuard:
    """
    Route protector builder that verifies a user's role capability and department boundaries.
    """
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    def __call__(self, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        allowed = check_permission(current_user.role, current_user.department, self.resource, self.action)
        if not allowed:
            # Record unauthorized attempt in audit log
            log_security_action(
                db=db,
                user_id=str(current_user.id),
                action="failed_access",
                resource=f"{self.resource}:{self.action}",
                status="denied"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. You lack the permission '{self.resource}:{self.action}'."
            )
        return True
