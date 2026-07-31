from app.database.session import SessionLocal
from app.database.models import Customer, Account, Card, Loan


def inspect_customers():
    """Print exact customer account details from Supabase database."""
    db = SessionLocal()
    try:
        customers = db.query(Customer).all()
        print(f"\n--- TOTAL CUSTOMERS IN SUPABASE DB: {len(customers)} ---\n")

        for cust in customers:
            accounts = db.query(Account).filter(Account.customer_id == cust.id).all()
            cards = db.query(Card).filter(Card.customer_id == cust.id).all()

            acc_str = ", ".join([f"{a.account_type} ({a.account_number} | Last4: {a.account_number[-4:]})" for a in accounts])
            card_str = ", ".join([f"{c.card_type} ({c.last_four})" for c in cards])

            print(f"Name: {cust.full_name}")
            print(f"DOB: {cust.dob}")
            print(f"Phone: {cust.phone_number}")
            print(f"Accounts: {acc_str}")
            print(f"Cards: {card_str}")
            print("-" * 50)
    finally:
        db.close()


if __name__ == "__main__":
    inspect_customers()
