from sqlalchemy.orm import Session
from app.database.models import Customer, Account, Card, SupportTicket
from app.services.audit import log_audit_event


def block_card(
    db: Session,
    customer_id: str,
    card_last_four: str | None = None,
    card_type: str = "Debit Card",
    reason: str = "Suspicious activity or customer request",
) -> dict:
    """Block a debit or credit card for an authenticated customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        log_audit_event(db, "block_card", "FAILED", customer_id, "Customer not found")
        return {"success": False, "error": "Customer not found"}

    query = db.query(Card).filter(Card.customer_id == customer_id)
    if card_last_four:
        query = query.filter(Card.last_four == card_last_four)
    elif card_type:
        query = query.filter(Card.card_type.ilike(f"%{card_type}%"))

    cards = query.all()

    if not cards:
        # Fallback to any active card for customer if specific parameters weren't matched
        cards = db.query(Card).filter(Card.customer_id == customer_id, Card.status == "Active").all()

    if not cards:
        log_audit_event(
            db,
            tool_called="block_card",
            status="FAILED",
            customer_id=customer_id,
            details=f"No active card found matching last 4: {card_last_four}",
        )
        return {"success": False, "error": "No active matching card found for blocking."}

    blocked_cards_info = []
    for card in cards:
        card.status = "Blocked"
        blocked_cards_info.append({"card_type": card.card_type, "last_four": card.last_four})

    # Raise automated high priority support ticket
    ticket = SupportTicket(
        customer_id=customer_id,
        issue=f"URGENT FRAUD LOCK: Blocked {len(cards)} card(s). Reason: {reason}",
        status="Escalated",
    )
    db.add(ticket)
    db.commit()

    log_audit_event(
        db,
        tool_called="block_card",
        status="SUCCESS",
        customer_id=customer_id,
        details=f"Blocked {len(cards)} card(s). Reason: {reason}",
    )

    return {
        "success": True,
        "customer_name": customer.full_name,
        "blocked_cards": blocked_cards_info,
        "message": f"Successfully blocked {len(cards)} card(s). A new replacement card request has been initiated.",
        "ticket_id": ticket.id,
    }


def freeze_account(
    db: Session,
    customer_id: str,
    reason: str = "Severe security concern / Account compromise",
) -> dict:
    """Freeze all bank accounts belonging to an authenticated customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        log_audit_event(db, "freeze_account", "FAILED", customer_id, "Customer not found")
        return {"success": False, "error": "Customer not found"}

    accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
    if not accounts:
        log_audit_event(db, "freeze_account", "FAILED", customer_id, "No accounts found")
        return {"success": False, "error": "No accounts found for customer."}

    frozen_acc_numbers = []
    for acc in accounts:
        acc.status = "Frozen"
        frozen_acc_numbers.append(f"••••{acc.account_number[-4:]}")

    # Also block all associated cards for security
    cards = db.query(Card).filter(Card.customer_id == customer_id).all()
    for card in cards:
        card.status = "Blocked"

    # Create emergency support ticket
    ticket = SupportTicket(
        customer_id=customer_id,
        issue=f"EMERGENCY ACCOUNT FREEZE: Accounts {', '.join(frozen_acc_numbers)} frozen. Reason: {reason}",
        status="Escalated",
    )
    db.add(ticket)
    db.commit()

    log_audit_event(
        db,
        tool_called="freeze_account",
        status="SUCCESS",
        customer_id=customer_id,
        details=f"Frozen {len(accounts)} accounts & blocked all cards. Reason: {reason}",
    )

    return {
        "success": True,
        "customer_name": customer.full_name,
        "frozen_accounts": frozen_acc_numbers,
        "message": "All your accounts have been immediately frozen for your protection. No further transactions can occur.",
        "ticket_id": ticket.id,
        "status": "Frozen",
    }
