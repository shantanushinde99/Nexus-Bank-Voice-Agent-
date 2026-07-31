import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_uuid)
    full_name = Column(String(120), nullable=False)
    phone_number = Column(String(20), nullable=False, unique=True)
    dob = Column(String(10), nullable=False)  # Format: YYYY-MM-DD or DD Month YYYY
    pin_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    cards = relationship("Card", back_populates="customer", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("SupportTicket", back_populates="customer", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="customer", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="customer", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    account_number = Column(String(20), nullable=False, unique=True)
    account_type = Column(String(30), nullable=False)  # Savings, Current, Salary
    balance = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="Active")  # Active, Frozen, Closed

    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # Debit, Credit
    merchant = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now)

    account = relationship("Account", back_populates="transactions")


class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    card_type = Column(String(30), nullable=False)  # Debit Card, Credit Card
    last_four = Column(String(4), nullable=False)
    status = Column(String(20), nullable=False, default="Active")  # Active, Blocked
    expiry_date = Column(String(7), nullable=False)  # MM/YY

    customer = relationship("Customer", back_populates="cards")


class Loan(Base):
    __tablename__ = "loans"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    loan_type = Column(String(50), nullable=False)  # Home Loan, Personal Loan, Auto Loan
    amount = Column(Float, nullable=False)
    emi = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)  # Annual percentage
    status = Column(String(20), nullable=False, default="Active")  # Active, Applied, Closed

    customer = relationship("Customer", back_populates="loans")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    issue = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="Open")  # Open, Escalated, Resolved
    created_at = Column(DateTime(timezone=True), default=utc_now)

    customer = relationship("Customer", back_populates="tickets")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    authenticated = Column(Boolean, default=False, nullable=False)
    call_id = Column(String(100), nullable=False, unique=True)
    failed_auth_attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    customer = relationship("Customer", back_populates="sessions")
    conversation_logs = relationship("ConversationLog", back_populates="session", cascade="all, delete-orphan")


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    speaker = Column(String(20), nullable=False)  # user, assistant, system
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("Session", back_populates="conversation_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    tool_called = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED, DENIED
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now)

    customer = relationship("Customer", back_populates="audit_logs")
