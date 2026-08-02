import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Customer, Account, Card, Loan, Transaction

def fetch_data():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("--- Rajesh Kumar ---")
    rajesh = db.query(Customer).filter(Customer.full_name == "Rajesh Kumar").first()
    if rajesh:
        print(f"DOB: {rajesh.dob}")
        print(f"PIN: 4321, Code Word: Mumbai")
        for acc in rajesh.accounts:
            print(f"Account: {acc.account_number}, Type: {acc.account_type}, Balance: {acc.balance}")
            # get recent transaction
            tx = db.query(Transaction).filter(Transaction.account_id == acc.id).order_by(Transaction.timestamp.desc()).first()
            if tx:
                print(f"Recent TX: {tx.amount} ({tx.transaction_type}) to {tx.merchant}")
        for card in rajesh.cards:
            print(f"Card: {card.last_four} ({card.card_type}), Status: {card.status}")
        for loan in rajesh.loans:
            print(f"Loan: {loan.amount} ({loan.loan_type}) EMI: {loan.emi}")
    else:
        print("Rajesh not found.")

    print("\n--- Priya Patel ---")
    priya = db.query(Customer).filter(Customer.full_name == "Priya Patel").first()
    if priya:
        print(f"DOB: {priya.dob}")
        print(f"PIN: 5678, Code Word: Desai")
        for acc in priya.accounts:
            print(f"Account: {acc.account_number}, Type: {acc.account_type}, Balance: {acc.balance}")
    else:
        print("Priya not found.")

if __name__ == "__main__":
    fetch_data()
