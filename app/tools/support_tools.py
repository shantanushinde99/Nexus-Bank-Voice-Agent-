from sqlalchemy.orm import Session
from app.database.models import Customer, SupportTicket, Session as CallSession
from app.services.audit import log_audit_event


def create_support_ticket(
    db: Session,
    customer_id: str | None,
    issue_description: str,
    category: str = "General Support",
) -> dict:
    """Create a new customer service ticket."""
    ticket = SupportTicket(
        customer_id=customer_id,
        issue=f"[{category}] {issue_description}",
        status="Open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    log_audit_event(
        db,
        tool_called="create_support_ticket",
        status="SUCCESS",
        customer_id=customer_id,
        details=f"Ticket ID: {ticket.id} | Category: {category}",
    )

    return {
        "success": True,
        "ticket_id": ticket.id,
        "issue": issue_description,
        "category": category,
        "status": "Open",
        "message": f"Support ticket #{ticket.id[:8]} created successfully. Our team will review your inquiry shortly.",
    }


def transfer_to_human(
    db: Session,
    reason: str,
    call_id: str | None = None,
    customer_id: str | None = None,
) -> dict:
    """Escalate customer session to a human representative."""
    # Create an escalated ticket
    ticket = SupportTicket(
        customer_id=customer_id,
        issue=f"HUMAN ESCALATION REQUEST: {reason}",
        status="Escalated",
    )
    db.add(ticket)
    db.commit()

    log_audit_event(
        db,
        tool_called="transfer_to_human",
        status="SUCCESS",
        customer_id=customer_id,
        details=f"Escalated to human agent. Reason: {reason}",
    )

    return {
        "success": True,
        "transfer": True,
        "destination": "Human Customer Support Tier 2",
        "reason": reason,
        "ticket_id": ticket.id,
        "message": f"I am transferring your call to a senior customer service agent right now. Please hold line. (Reason: {reason})",
    }
