import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Customer, Account, Session as CallSession
from app.services.audit import log_audit_event
from app.services.memory import MemoryManager


def normalize_dob(dob_str: str) -> str:
    """Normalize various date of birth spoken formats to YYYY-MM-DD."""
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", dob_str.strip())

    formats = [
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%B %d %Y",
        "%b %d %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return dob_str.strip()


def verify_customer(
    db: Session,
    account_last_four: str,
    dob: str,
    call_id: str | None = None,
) -> dict:
    """Verify customer identity by last 4 digits of account number and date of birth."""
    account_last_four = account_last_four.strip()
    normalized_dob = normalize_dob(dob)

    # Search for customer matching DOB and account ending with account_last_four
    query = (
        db.query(Customer)
        .join(Account, Account.customer_id == Customer.id)
        .filter((Customer.dob == normalized_dob) | (Customer.dob == dob.strip()))
        .filter(Account.account_number.endswith(account_last_four))
    )
    customer = query.first()

    session: CallSession | None = None
    if call_id:
        session = MemoryManager.get_or_create_session(db, call_id)

    if customer:
        if session:
            MemoryManager.set_authenticated(db, session, customer.id)

        log_audit_event(
            db=db,
            tool_called="verify_customer",
            status="SUCCESS",
            customer_id=customer.id,
            details=f"Verified with last 4: {account_last_four}, DOB: {normalized_dob}",
        )
        return {
            "success": True,
            "message": f"Authentication successful for {customer.full_name}.",
            "customer_id": customer.id,
            "full_name": customer.full_name,
            "failed_attempts": 0,
        }

    # Handle authentication failure
    failed_attempts = 1
    if session:
        failed_attempts = MemoryManager.record_failed_auth(db, session)

    log_audit_event(
        db=db,
        tool_called="verify_customer",
        status="FAILED",
        customer_id=None,
        details=f"Auth failed for account ending: {account_last_four}, DOB: {dob} (Normalized: {normalized_dob})",
    )

    should_escalate = failed_attempts >= 3

    return {
        "success": False,
        "message": "Authentication failed. Details provided do not match our records.",
        "customer_id": None,
        "failed_attempts": failed_attempts,
        "should_escalate": should_escalate,
    }
