"""
Comprehensive tests for Finance Tracker Backend:
Covers user registration, login, JWT auth, transaction CRUD, analytics, and error cases using FastAPI's TestClient.
Requires: pytest, .env with JWT_SECRET set in project root.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Patch DB for testing (set DB_URL before importing app)
@pytest.fixture(scope="session", autouse=True)
def test_db_env(monkeypatch):
    # Use a temp file for SQLite DB (persist for all tests, remove after)
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_url = f"sqlite:///{tmp_db.name}"
    monkeypatch.setenv("DB_URL", db_url)
    # Set a secure JWT secret for test runs
    monkeypatch.setenv("JWT_SECRET", "testsecret12345")
    yield
    os.unlink(tmp_db.name)

# Import after monkeypatching env for DB/JWT
from src.api.main import app
from src.api.db import Base, engine

client = TestClient(app)


def clear_db():
    # Drop and re-create all tables for test isolation
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def run_around_tests():
    clear_db()
    yield
    clear_db()


def test_health_check():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def register_user(email="testuser@example.com", password="StrongPassword!9"):
    resp = client.post("/auth/register", json={"email": email, "password": password})
    return resp


def login_user(email="testuser@example.com", password="StrongPassword!9"):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp


def get_jwt_token(email="testuser@example.com", password="StrongPassword!9"):
    register_user(email, password)
    resp = login_user(email, password)
    return resp.json()["access_token"]


def test_register_success():
    resp = register_user()
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_register_duplicate_email():
    register_user()
    resp = register_user()
    assert resp.status_code == 400
    j = resp.json()
    assert "already registered" in j.get("message") or "already registered" in j.get("detail", "")


def test_login_success():
    register_user()
    resp = login_user()
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_invalid_password():
    register_user()
    resp = login_user(password="wrongpassword")
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json().get("message", "")


def test_login_nonexistent_email():
    resp = login_user(email="nobody@foo.com")
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json().get("message", "")


def test_transactions_crud_lifecycle():
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create a transaction
    txn = {
        "amount": 99.99,
        "category": "Groceries",
        "description": "Test food",
        "type": "expense"
    }
    resp = client.post("/transactions/", json=txn, headers=headers)
    assert resp.status_code == 200
    txn_id = resp.json()["id"]

    # Get transactions
    resp = client.get("/transactions/", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert any(t["id"] == txn_id for t in results)
    assert results[0]["amount"] == 99.99

    # Update the transaction
    update_data = dict(txn)
    update_data["amount"] = 120
    resp = client.put(f"/transactions/{txn_id}", json=update_data, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["amount"] == 120

    # Delete the transaction
    resp = client.delete(f"/transactions/{txn_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"]

    # Ensure it is gone
    resp = client.get("/transactions/", headers=headers)
    assert resp.status_code == 200
    assert txn_id not in [t["id"] for t in resp.json()]


def test_transaction_delete_missing():
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}
    # Try to delete ID that does not exist
    resp = client.delete("/transactions/99999", headers=headers)
    assert resp.status_code == 404
    assert "not found" in resp.json().get("message", "")


def test_transaction_update_missing():
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.put("/transactions/42", json={
        "amount": 8, "category": "Misc", "description": "", "type": "expense"
    }, headers=headers)
    assert resp.status_code == 404
    assert "not found" in resp.json().get("message", "")


def test_protected_endpoint_requires_jwt():
    # Not providing JWT
    resp = client.get("/transactions/")
    assert resp.status_code in (401, 403)
    # Malformed JWT
    headers = {"Authorization": "Bearer foobar.invalid.jwt"}
    resp = client.get("/transactions/", headers=headers)
    assert resp.status_code == 401


def test_analytics_summary():
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Add 2 income and 1 expense
    txns = [
        {"amount": 500, "category": "Salary", "description": "", "type": "income"},
        {"amount": 200, "category": "Salary", "description": "", "type": "income"},
        {"amount": 100, "category": "Food", "description": "", "type": "expense"},
    ]
    for t in txns:
        client.post("/transactions/", json={**t, "date": None}, headers=headers)
    resp = client.get("/transactions/analytics/summary", headers=headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_income"] == 700.0
    assert summary["total_expense"] == 100.0
    assert summary["per_category"]["Salary"] == 700.0
    assert summary["per_category"]["Food"] == 100.0


@pytest.mark.parametrize("route", ["/transactions/", "/transactions/analytics/summary"])
def test_jwt_required_all_transactions_endpoints(route):
    resp = client.get(route)
    assert resp.status_code in (401, 403)

def test_docs_usage():
    resp = client.get("/api-usage")
    assert resp.status_code == 200
    assert "JWT token" in resp.json().get("message", "")

def test_validation_error_reporting():
    # Transaction create with missing fields
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/transactions/", json={
        "category": "TestOnly"
    }, headers=headers)
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data

"""
Manual setup required:
- Create a `.env` file in the root of the finance-tracker-and-budgeting-app-594b2fca project with at least:
    JWT_SECRET=anylongrandomstring
  (Optional) DB_URL is overridden in tests, but in dev/server mode, set as needed.

Run tests:
    cd finance-tracker-and-budgeting-app-594b2fca/finance_tracker_backend
    pytest

The suite will auto-initialize and clean the test DB before/after every test function.
"""
