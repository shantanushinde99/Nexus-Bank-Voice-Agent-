import hashlib
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database.session import engine, init_db, SessionLocal
from app.database.models import Customer, Account, Transaction, Card, Loan, SupportTicket


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


MERCHANTS = [
    "Swiggy India",
    "Zomato Food Delivery",
    "Amazon India",
    "Reliance Fresh Supermarket",
    "D-Mart Retail",
    "Flipkart Online",
    "Uber India Rides",
    "Tata Power Electricity",
    "SBI ATM Cash Withdrawal",
    "BigBasket Grocery",
    "Indian Oil Petrol Pump",
    "BookMyShow Movie Tickets",
    "Apollo Pharmacy",
    "Airtel Broadband Bill",
    "Dominos Pizza India",
]

INDIAN_CUSTOMERS = [
    {"name": "Aarav Sharma", "phone": "+919876543210", "dob": "1999-08-14", "pin": "1234"},
    {"name": "Priya Patel", "phone": "+919876543211", "dob": "1995-03-22", "pin": "5678"},
    {"name": "Rajesh Kumar", "phone": "+919876543212", "dob": "1988-11-05", "pin": "4321"},
    {"name": "Ananya Iyer", "phone": "+919876543213", "dob": "2001-01-30", "pin": "8765"},
    {"name": "Vikram Singh", "phone": "+919876543214", "dob": "1992-07-19", "pin": "9999"},
    {"name": "Deepika Rao", "phone": "+919876543215", "dob": "1997-12-10", "pin": "1111"},
    {"name": "Rohan Gupta", "phone": "+919876543216", "dob": "1990-05-25", "pin": "2222"},
    {"name": "Kavya Reddy", "phone": "+919876543217", "dob": "1998-09-08", "pin": "3333"},
    {"name": "Aditya Joshi", "phone": "+919876543218", "dob": "1985-04-12", "pin": "4444"},
    {"name": "Meera Nair", "phone": "+919876543219", "dob": "1996-06-17", "pin": "5555"},
]


def seed_database():
    """Populate database with 10 customers, 15 accounts, 200 transactions, 20 cards, 5 loans, 15 tickets."""
    init_db()
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Customer).count() >= 10:
            print("Database is already seeded with customer data.")
            return

        print("Seeding database with realistic Indian banking demo data...")

        created_customers = []
        created_accounts = []

        # 1. Seed 10 Customers
        account_number_seq = 1000004567
        for idx, cust_info in enumerate(INDIAN_CUSTOMERS):
            cust = Customer(
                full_name=cust_info["name"],
                phone_number=cust_info["phone"],
                dob=cust_info["dob"],
                pin_hash=hash_pin(cust_info["pin"]),
            )
            db.add(cust)
            db.flush()
            created_customers.append(cust)

            # Assign 1 to 2 accounts per customer (Total 15 accounts)
            num_accounts = 2 if idx < 5 else 1
            for a_idx in range(num_accounts):
                acc_type = "Savings" if a_idx == 0 else "Current"
                acc_num = str(account_number_seq)
                account_number_seq += 1111

                # Specific balance for test user (Aarav Sharma - last 4: 4567, DOB: 1999-08-14)
                if idx == 0 and a_idx == 0:
                    balance = 125430.00
                    acc_num = "9876544567"
                else:
                    balance = round(random.uniform(5000.0, 350000.0), 2)

                account = Account(
                    customer_id=cust.id,
                    account_number=acc_num,
                    account_type=acc_type,
                    balance=balance,
                    status="Active",
                )
                db.add(account)
                db.flush()
                created_accounts.append(account)

        # 2. Seed 20 Cards (2 per customer)
        card_seq = 4111
        for cust in created_customers:
            debit_card = Card(
                customer_id=cust.id,
                card_type="Debit Card",
                last_four=str(card_seq),
                status="Active",
                expiry_date="08/28",
            )
            card_seq += 123
            credit_card = Card(
                customer_id=cust.id,
                card_type="Credit Card",
                last_four=str(card_seq),
                status="Active",
                expiry_date="11/29",
            )
            card_seq += 234
            db.add_all([debit_card, credit_card])

        # 3. Seed 5 Loans
        loan_types = [
            ("Home Loan", 4500000.0, 42150.0, 8.5),
            ("Personal Loan", 300000.0, 9500.0, 11.5),
            ("Auto Loan", 750000.0, 16200.0, 9.25),
            ("Education Loan", 1200000.0, 14800.0, 8.75),
            ("Personal Loan", 150000.0, 5200.0, 12.0),
        ]
        for idx, (l_type, amount, emi, rate) in enumerate(loan_types):
            loan = Loan(
                customer_id=created_customers[idx].id,
                loan_type=l_type,
                amount=amount,
                emi=emi,
                interest_rate=rate,
                status="Active",
            )
            db.add(loan)

        # 4. Seed 200 Transactions across accounts
        now = datetime.now(timezone.utc)
        for i in range(200):
            acc = random.choice(created_accounts)
            is_credit = random.random() < 0.25
            t_type = "Credit" if is_credit else "Debit"
            merchant = None if is_credit else random.choice(MERCHANTS)
            desc = "Salary Credit" if is_credit else f"Payment to {merchant}"

            amount = round(random.uniform(150.0, 25000.0) if not is_credit else random.uniform(25000.0, 85000.0), 2)
            timestamp = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))

            tx = Transaction(
                account_id=acc.id,
                amount=amount,
                transaction_type=t_type,
                merchant=merchant,
                description=desc,
                timestamp=timestamp,
            )
            db.add(tx)

        # 5. Seed 15 Support Tickets
        issues = [
            "ATM transaction debited but cash not dispensed",
            "Inquiry regarding credit card reward points redemption",
            "Request for monthly e-statement on email",
            "Update residential address in bank profile",
            "Inquiry about fixed deposit interest rates",
            "UPI transaction failed but money deducted",
            "Request for new cheque book dispatch",
            "International transaction enablement request",
            "Query regarding home loan EMI deduction date",
            "Debit card PIN reset request",
            "Mobile banking app login issue",
            "Duplicate transaction deduction reported",
            "Request for credit limit increase",
            "Interest certificate request for tax filing",
            "Branch appointment booking for locker opening",
        ]
        for idx in range(15):
            cust = created_customers[idx % len(created_customers)]
            ticket = SupportTicket(
                customer_id=cust.id,
                issue=issues[idx],
                status="Open" if idx % 2 == 0 else "Resolved",
                created_at=now - timedelta(days=random.randint(1, 15)),
            )
            db.add(ticket)

        db.commit()
        print("Database successfully seeded with demo banking data!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
