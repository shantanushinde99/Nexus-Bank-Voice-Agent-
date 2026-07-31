import uuid
import pytest
from app.agents.coordinator import CoordinatorAgent
from app.database.session import SessionLocal, init_db
from app.database.seed import seed_database


@pytest.fixture(scope="module")
def setup_db():
    init_db()
    seed_database()


def test_coordinator_greeting(setup_db):
    db = SessionLocal()
    res = CoordinatorAgent.process_call(db, call_id=f"test-greet-{uuid.uuid4()}", user_message="Hello")
    assert res["session_id"] is not None
    assert "Welcome to Nexus Financial" in res["response_text"]
    db.close()


def test_coordinator_unauthenticated_balance_request(setup_db):
    db = SessionLocal()
    res = CoordinatorAgent.process_call(db, call_id=f"test-unauth-{uuid.uuid4()}", user_message="What is my account balance?")
    assert res["authenticated"] is False
    assert res["auth_prompt"] is True
    assert "verify your identity" in res["response_text"]
    db.close()


def test_coordinator_full_authenticated_flow(setup_db):
    db = SessionLocal()
    call_id = f"test-flow-{uuid.uuid4()}"

    # Step 1: Request balance -> Prompt for auth
    step1 = CoordinatorAgent.process_call(db, call_id=call_id, user_message="What is my balance?")
    assert step1["auth_prompt"] is True

    # Step 2: Provide Last 4 digits (4567) and DOB (1999-08-14)
    step2 = CoordinatorAgent.process_call(db, call_id=call_id, user_message="Account 4567 and DOB is 1999-08-14")
    assert step2["authenticated"] is True
    assert "Authentication successful" in step2["response_text"]

    # Step 3: Now ask for balance -> Balance returned without asking for auth again!
    step3 = CoordinatorAgent.process_call(db, call_id=call_id, user_message="Show me my balance")
    assert step3["authenticated"] is True
    assert step3["agent"] == "BankingAgent"
    assert "total account balance" in step3["response_text"].lower()

    # Step 4: Ask recent transactions -> Works seamlessly using session memory context!
    step4 = CoordinatorAgent.process_call(db, call_id=call_id, user_message="What about my recent transactions?")
    assert step4["authenticated"] is True
    assert step4["agent"] == "BankingAgent"

    db.close()


def test_coordinator_human_escalation(setup_db):
    db = SessionLocal()
    res = CoordinatorAgent.process_call(db, call_id=f"test-esc-{uuid.uuid4()}", user_message="I want to speak to a human representative")
    assert res["transfer_human"] is True
    assert "transferring your call" in res["response_text"].lower()
    db.close()
