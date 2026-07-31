from sqlalchemy.orm import Session
from app.database.models import Customer, Account, Transaction, Card
from app.services.audit import log_audit_event


def get_balance(db: Session, customer_id: str) -> dict:
    """Retrieve account balances for an authenticated customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        log_audit_event(db, "get_balance", "FAILED", customer_id, "Customer not found")
        return {"success": False, "error": "Customer not found"}

    accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
    accounts_data = [
        {
            "account_id": acc.id,
            "account_number": f"••••{acc.account_number[-4:]}",
            "full_account_number": acc.account_number,
            "account_type": acc.account_type,
            "balance": acc.balance,
            "formatted_balance": f"₹{acc.balance:,.2f}",
            "status": acc.status,
        }
        for acc in accounts
    ]

    total_balance = sum(acc.balance for acc in accounts)

    log_audit_event(
        db,
        tool_called="get_balance",
        status="SUCCESS",
        customer_id=customer_id,
        details=f"Retrieved {len(accounts)} accounts. Total: ₹{total_balance:,.2f}",
    )

    return {
        "success": True,
        "customer_name": customer.full_name,
        "accounts": accounts_data,
        "total_balance": total_balance,
        "formatted_total_balance": f"₹{total_balance:,.2f}",
    }


def get_recent_transactions(db: Session, customer_id: str, limit: int = 5) -> dict:
    """Fetch recent transactions for an authenticated customer across all accounts."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        log_audit_event(db, "get_recent_transactions", "FAILED", customer_id, "Customer not found")
        return {"success": False, "error": "Customer not found"}

    transactions = (
        db.query(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .filter(Account.customer_id == customer_id)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )

    tx_list = [
        {
            "transaction_id": tx.id,
            "amount": tx.amount,
            "formatted_amount": f"₹{tx.amount:,.2f}",
            "type": tx.transaction_type,
            "merchant": tx.merchant or "N/A",
            "description": tx.description or "",
            "timestamp": tx.timestamp.strftime("%d %b %Y, %I:%M %p"),
        }
        for tx in transactions
    ]

    log_audit_event(
        db,
        tool_called="get_recent_transactions",
        status="SUCCESS",
        customer_id=customer_id,
        details=f"Retrieved {len(tx_list)} transactions",
    )

    return {
        "success": True,
        "customer_name": customer.full_name,
        "transactions": tx_list,
        "count": len(tx_list),
    }


def get_account_details(db: Session, customer_id: str) -> dict:
    """Retrieve full customer profile and associated accounts summary."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        log_audit_event(db, "get_account_details", "FAILED", customer_id, "Customer not found")
        return {"success": False, "error": "Customer not found"}

    accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
    accounts_info = [
        {
            "account_number": f"••••{acc.account_number[-4:]}",
            "account_type": acc.account_type,
            "balance": f"₹{acc.balance:,.2f}",
            "status": acc.status,
        }
        for acc in accounts
    ]

    cards = db.query(Card).filter(Card.customer_id == customer_id).all()
    cards_info = [
        {
            "card_type": c.card_type,
            "last_four": c.last_four,
            "status": c.status,
        }
        for c in cards
    ]

    log_audit_event(
        db,
        tool_called="get_account_details",
        status="SUCCESS",
        customer_id=customer_id,
        details="Retrieved customer account profile and cards",
    )

    acc_summary_text = ", ".join([f"{a['account_type']} (ending {a['account_number']}) with balance {a['balance']} [{a['status']}]" for a in accounts_info])
    card_summary_text = ", ".join([f"{c['card_type']} ending {c['last_four']} is {c['status']}" for c in cards_info])

    return {
        "success": True,
        "customer_id": customer.id,
        "full_name": customer.full_name,
        "phone_number": customer.phone_number,
        "dob": customer.dob,
        "accounts": accounts_info,
        "cards": cards_info,
        "summary": f"{customer.full_name} has {len(accounts_info)} account(s): {acc_summary_text}. Cards: {card_summary_text}.",
    }
