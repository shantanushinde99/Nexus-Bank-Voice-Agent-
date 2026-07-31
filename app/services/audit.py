from sqlalchemy.orm import Session
from app.database.models import AuditLog
from app.services.logging import logger


def log_audit_event(
    db: Session,
    tool_called: str,
    status: str,
    customer_id: str | None = None,
    details: str | None = None,
) -> AuditLog:
    """Record an audit entry in the database for every backend tool invocation."""
    try:
        audit_entry = AuditLog(
            customer_id=customer_id,
            tool_called=tool_called,
            status=status,
            details=details,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        logger.info(
            f"[AUDIT] Tool: '{tool_called}' | Customer: {customer_id or 'Anonymous'} | Status: {status} | Details: {details or ''}"
        )
        return audit_entry
    except Exception as e:
        db.rollback()
        logger.error(f"[AUDIT ERROR] Failed to record audit log for {tool_called}: {e}")
        raise
