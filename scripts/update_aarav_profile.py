from app.database.session import SessionLocal
from app.database.models import Customer, Account, Card, Loan


def update_aarav_profile():
    """Update Aarav Sharma's card to 4567 and loan EMI to 4200.0 in database."""
    db = SessionLocal()
    try:
        aarav = db.query(Customer).filter(Customer.full_name == "Aarav Sharma").first()
        if not aarav:
            print("Customer Aarav Sharma not found.")
            return

        print(f"Updating profile for Aarav Sharma (ID: {aarav.id})...")

        # 1. Update Debit Card to 4567
        debit_card = db.query(Card).filter(Card.customer_id == aarav.id, Card.card_type == "Debit Card").first()
        if debit_card:
            debit_card.last_four = "4567"
            debit_card.status = "Active"
            print("Updated Debit Card last 4 digits to '4567'")

        # 2. Update existing loan EMI to 4200.0
        aarav_loan = db.query(Loan).filter(Loan.customer_id == aarav.id).first()
        if aarav_loan:
            aarav_loan.emi = 4200.0
            aarav_loan.amount = 300000.0
            print("Updated existing loan EMI to RS 4,200.00")

        db.commit()
        print("Aarav Sharma profile updated successfully in Supabase database!")
    except Exception as e:
        db.rollback()
        print(f"Error updating profile: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    update_aarav_profile()
