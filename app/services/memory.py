from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database.models import Session as CallSession, ConversationLog
from app.services.logging import logger


class MemoryManager:
    """Manages active call session state and conversation logs."""

    @staticmethod
    def get_or_create_session(db: Session, call_id: str, customer_id: str | None = None) -> CallSession:
        """Fetch existing session by call_id or create a new session."""
        session = db.query(CallSession).filter(CallSession.call_id == call_id).first()
        if not session:
            session = CallSession(
                call_id=call_id,
                customer_id=customer_id,
                authenticated=False,
                failed_auth_attempts=0,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"[MEMORY] Created new session for call_id: {call_id}")
        return session

    @staticmethod
    def log_message(db: Session, session_id: str, speaker: str, message: str) -> ConversationLog:
        """Log a turn in the conversation history."""
        log_entry = ConversationLog(
            session_id=session_id,
            speaker=speaker,
            message=message,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def get_conversation_history(db: Session, session_id: str, limit: int = 20) -> list[dict]:
        """Fetch recent turns from conversation log."""
        logs = (
            db.query(ConversationLog)
            .filter(ConversationLog.session_id == session_id)
            .order_by(ConversationLog.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [{"speaker": log.speaker, "message": log.message, "timestamp": log.timestamp.isoformat()} for log in logs]

    @staticmethod
    def set_authenticated(db: Session, session: CallSession, customer_id: str) -> CallSession:
        """Mark session as authenticated for the active customer."""
        session.authenticated = True
        session.customer_id = customer_id
        session.failed_auth_attempts = 0
        db.commit()
        db.refresh(session)
        logger.info(f"[MEMORY] Session '{session.call_id}' authenticated for customer '{customer_id}'")
        return session

    @staticmethod
    def record_failed_auth(db: Session, session: CallSession) -> int:
        """Record an authentication failure attempt and return current failure count."""
        session.failed_auth_attempts += 1
        db.commit()
        db.refresh(session)
        logger.warning(
            f"[MEMORY] Failed auth attempt #{session.failed_auth_attempts} for call_id: {session.call_id}"
        )
        return session.failed_auth_attempts
