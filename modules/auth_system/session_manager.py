import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from modules.auth_system.models import UserSession

logger = logging.getLogger(__name__)

def create_session(db: Session, user_id: str, refresh_token: str, ip_address: str | None = None) -> UserSession:
    """
    Creates a new user session associated with a refresh token.
    """
    import uuid
    u_uuid = uuid.UUID(user_id)
    
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    session = UserSession(
        user_id=u_uuid,
        refresh_token=refresh_token,
        ip_address=ip_address,
        expires_at=expires_at,
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def invalidate_session(db: Session, session_id: str):
    """
    Terminates a single session.
    """
    import uuid
    try:
        s_uuid = uuid.UUID(session_id)
        session = db.query(UserSession).filter(UserSession.id == s_uuid).first()
        if session:
            session.is_active = False
            db.commit()
    except ValueError:
        pass

def invalidate_all_user_sessions(db: Session, user_id: str):
    """
    Logs out user from all active sessions across devices.
    """
    import uuid
    try:
        u_uuid = uuid.UUID(user_id)
        sessions = db.query(UserSession).filter(
            UserSession.user_id == u_uuid,
            UserSession.is_active == True
        ).all()
        for s in sessions:
            s.is_active = False
        db.commit()
    except ValueError:
        pass

def is_session_valid(db: Session, refresh_token: str) -> bool:
    """
    Validates if a session refresh token is active and not expired.
    """
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.is_active == True
    ).first()
    if not session:
        return False
    now = datetime.utcnow()
    expires = session.expires_at
    if expires.tzinfo is not None:
        from datetime import timezone
        now = datetime.now(timezone.utc)
    if expires < now:
        session.is_active = False
        db.commit()
        return False
    return True
