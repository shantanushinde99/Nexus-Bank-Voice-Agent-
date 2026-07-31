import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, Customer, Account, Card, Loan, AuditLog
from app.database.seed import seed_database
from app.tools import auth_tools, banking_tools, loan_tools, fraud_tools, support_tools

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed test data
    from app.database.models import Customer, Account
    from app.database.seed import hash_pin

    c = Customer(
        full_name="Aarav Sharma",
        phone_number="+919876543210",
        dob="1999-08-14",
        pin_hash=hash_pin("1234"),
    )
    db.add(c)
    db.flush()

    acc = Account(
        customer_id=c.id,
        account_number="9876544567",
        account_type="Savings",
        balance=125430.0,
        status="Active",
    )
    card = Card(
        customer_id=c.id,
        card_type="Debit Card",
        last_four="4567",
        status="Active",
        expiry_date="12/28",
    )
    db.add_all([acc, card])
    db.commit()

    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_auth_tools_success(db_session):
    res = auth_tools.verify_customer(db_session, account_last_four="4567", dob="1999-08-14", call_id="test-call-1")
    assert res["success"] is True
    assert res["full_name"] == "Aarav Sharma"

    # Verify Audit Log entry
    audit = db_session.query(AuditLog).filter(AuditLog.tool_called == "verify_customer").first()
    assert audit is not None
    assert audit.status == "SUCCESS"


def test_auth_tools_failure(db_session):
    res = auth_tools.verify_customer(db_session, account_last_four="9999", dob="1999-08-14", call_id="test-call-2")
    assert res["success"] is False
    assert res["failed_attempts"] == 1


def test_banking_tools(db_session):
    customer = db_session.query(Customer).first()
    res = banking_tools.get_balance(db_session, customer.id)
    assert res["success"] is True
    assert res["total_balance"] == 125430.0
    assert "₹125,430.00" in res["formatted_total_balance"]


def test_loan_tools_emi_and_eligibility(db_session):
    emi_res = loan_tools.calculate_emi(principal=100000, annual_interest_rate=10.0, tenure_months=12)
    assert emi_res["success"] is True
    assert emi_res["monthly_emi"] > 0

    customer = db_session.query(Customer).first()
    eligibility = loan_tools.check_loan_eligibility(db_session, customer.id, requested_amount=200000)
    assert eligibility["success"] is True
    assert eligibility["is_eligible"] is True


def test_fraud_tools_block_card(db_session):
    customer = db_session.query(Customer).first()
    res = fraud_tools.block_card(db_session, customer.id, card_last_four="4567")
    assert res["success"] is True
    assert res["blocked_cards"][0]["last_four"] == "4567"

    card = db_session.query(Card).filter(Card.customer_id == customer.id).first()
    assert card.status == "Blocked"
