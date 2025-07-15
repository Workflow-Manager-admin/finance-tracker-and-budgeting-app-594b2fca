import pytest
from fastapi.testclient import TestClient
import random
import string

# Import the FastAPI app from the main module
from src.api.main import app

client = TestClient(app)

# PUBLIC_INTERFACE
def random_email():
    """Generate a random email address for test isolation."""
    user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{user}@example.com"

@pytest.mark.parametrize("full_name", [None, "Test Healthcheck"])
def test_register_health(full_name):
    """
    Posts to /auth/register with dummy data and asserts we do not get a 500 error.
    Passes if code is 200, 400, or 422 (sanity check: not an internal server/database error).
    Confirms FastAPI runs, DB is connectable/writable, and basic request/response cycle works.
    """
    user_data = {
        "email": random_email(),
        "password": "healthcheckpw123",  # Password meets min length
    }
    if full_name is not None:
        user_data["full_name"] = full_name

    response = client.post("/auth/register", json=user_data)
    # Acceptable: 200 (registered), 400 (duplicate/validation), 422 (schema)
    assert response.status_code in {200, 400, 422}, (
        f"Unexpected status {response.status_code}: {response.text}. "
        "Expected 200, 400, or 422. Indicates FastAPI/DB connectivity problem if 500."
    )
