import sys
import os

# Dynamically add the 'src' directory to sys.path relative to this test file,
# regardless of invocation directory (works whether pytest is run from root or backend folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Up two levels from this test file to reach the project root, then add src to sys.path.
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
src_path = os.path.join(project_root, "finance_tracker_backend", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

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

def test_register_and_login_success():
    """
    Registers a new user and ensures login with same credentials succeeds.
    Fails (with printed error) if login does not work after successful registration.
    """
    test_email = random_email()
    test_password = "validTestPassword1!"
    reg_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test user"
    }
    # Register user
    reg_response = client.post("/auth/register", json=reg_data)
    assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"

    # Login user
    login_response = client.post(
        "/auth/login",
        data={"username": test_email, "password": test_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200, (
        f"Login failed after registration (expected 200, got {login_response.status_code}): {login_response.text}"
    )
    # Should return access token and user details
    resp_data = login_response.json()
    assert "access_token" in resp_data and resp_data["token_type"] == "bearer"
    assert resp_data.get("user", {}).get("email") == test_email

def test_register_and_login_wrong_password():
    """
    Registers a new user and checks that login with wrong password fails.
    """
    test_email = random_email()
    test_password = "AnotherValidPass1!"
    reg_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test user"
    }
    # Register user
    reg_response = client.post("/auth/register", json=reg_data)
    assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"

    bad_password = "WRONGpass123!"
    # Attempt login with wrong password
    login_response = client.post(
        "/auth/login",
        data={"username": test_email, "password": bad_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 401, (
        f"Login with wrong password should fail (got {login_response.status_code}): {login_response.text}"
    )
    assert "Incorrect email or password" in login_response.text

