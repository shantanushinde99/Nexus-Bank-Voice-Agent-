import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import get_db, SessionLocal
from app.database.models import Customer

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_verify_user_endpoint():
    # Test authentication with seeded customer Aarav Sharma (last 4: 4567, DOB: 1999-08-14)
    response = client.post(
        "/api/verify-user",
        json={"account_last_four": "4567", "dob": "1999-08-14", "call_id": "api-test-call"},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["full_name"] == "Aarav Sharma"


def test_balance_endpoint():
    db = SessionLocal()
    cust = db.query(Customer).filter(Customer.full_name == "Aarav Sharma").first()
    if cust:
        response = client.get(f"/api/balance/{cust.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_balance"] > 0
    db.close()
