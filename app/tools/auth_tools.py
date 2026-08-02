import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Customer, Account, Session as CallSession
from app.services.audit import log_audit_event
from app.services.memory import MemoryManager
from app.database.seed import hash_pin


def normalize_dob(dob_str: str) -> str:
    """Normalize various date of birth spoken formats to YYYY-MM-DD."""
    cleaned = dob_str.strip().lower()
    
    ordinals = {
        "first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5",
        "sixth": "6", "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10",
        "eleventh": "11", "twelfth": "12", "thirteenth": "13", "fourteenth": "14", "fifteenth": "15",
        "sixteenth": "16", "seventeenth": "17", "eighteenth": "18", "nineteenth": "19", "twentieth": "20",
        "twenty first": "21", "twenty-first": "21", "twenty second": "22", "twenty-second": "22",
        "twenty third": "23", "twenty-third": "23", "twenty fourth": "24", "twenty-fourth": "24",
        "twenty fifth": "25", "twenty-fifth": "25", "twenty sixth": "26", "twenty-sixth": "26",
        "twenty seventh": "27", "twenty-seventh": "27", "twenty eighth": "28", "twenty-eighth": "28",
        "twenty ninth": "29", "twenty-ninth": "29", "thirtieth": "30",
        "thirty first": "31", "thirty-first": "31"
    }
    
    for word, num in ordinals.items():
        if word in cleaned:
            cleaned = cleaned.replace(word, num)
            
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", cleaned)
    cleaned = " ".join(cleaned.split())

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
            # datetime.strptime is case-insensitive for month names
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return dob_str.strip()


def verify_customer(
    db: Session,
    account_last_four: str,
    dob: str,
    pin: str,
    code_word: str,
    call_id: str | None = None,
) -> dict:
    """Verify customer identity by last 4 digits of account number and date of birth."""
    account_last_four = account_last_four.strip()
    
    if not pin or not code_word:
        return {
            "success": False,
            "message": "Authentication failed. The tool requires 'pin' and 'code_word'. Please ask the user for their 4-digit PIN and their secret code word.",
            "customer_id": None,
            "failed_attempts": 0,
            "should_escalate": False,
        }

    normalized_dob = normalize_dob(dob)
    
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", normalized_dob):
        return {
            "success": False,
            "message": "Authentication failed. The date of birth format is invalid. Please ask the user to provide it again.",
            "customer_id": None,
            "failed_attempts": 0,
            "should_escalate": False,
        }

    hashed_pin = hash_pin(pin.strip())
    hashed_code_word = hash_pin(code_word.strip().lower())

    # Search for customer matching DOB, PIN, code word and account ending with account_last_four
    query = (
        db.query(Customer)
        .join(Account, Account.customer_id == Customer.id)
        .filter(Customer.dob == normalized_dob)
        .filter(Customer.pin_hash == hashed_pin)
        .filter(Customer.code_word_hash == hashed_code_word)
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


def get_security_question(
    db: Session,
    account_last_four: str,
    dob: str,
) -> dict:
    """Fetch the security question for a customer before final verification."""
    account_last_four = account_last_four.strip()
    normalized_dob = normalize_dob(dob)

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", normalized_dob):
        return {
            "success": False,
            "message": "I could not understand the date of birth. Please ask the user to provide it again clearly."
        }

    query = (
        db.query(Customer)
        .join(Account, Account.customer_id == Customer.id)
        .filter(Customer.dob == normalized_dob)
        .filter(Account.account_number.endswith(account_last_four))
    )
    customer = query.first()

    if not customer:
        return {
            "success": False,
            "message": "We could not find an account matching that account number and date of birth. Please ask the user to provide them again."
        }

    return {
        "success": True,
        "security_question": customer.security_question
    }
