import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from services.user_service import UserService, ValidationError

import pytest

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-token-123"}


# ---------------------------------------------------------------------------
# Existing endpoint tests
# ---------------------------------------------------------------------------

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_users_success():
    response = client.get("/api/users", headers=AUTH_HEADERS)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 1


def test_get_users_no_auth():
    response = client.get("/api/users")
    assert response.status_code == 401


def test_get_user_by_id():
    response = client.get("/api/users/1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_user_not_found():
    response = client.get("/api/users/999", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_create_user():
    payload = {"name": "Test User", "email": "test@example.com", "role": "user"}
    response = client.post("/api/users", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 201
    assert response.json()["name"] == "Test User"


# ---------------------------------------------------------------------------
# Input validation tests – UserService._validate_user_input / create_user
# ---------------------------------------------------------------------------

class TestUserServiceValidation:
    """Unit tests for input validation in UserService."""

    def setup_method(self):
        self.service = UserService()

    # --- None checks ---

    def test_create_user_name_none_raises(self):
        from models.user import UserCreate
        user = UserCreate(name="placeholder", email="a@b.com", role="user")
        user.name = None  # bypass pydantic for direct service test
        with pytest.raises(ValidationError, match="None"):
            self.service.create_user(user)

    def test_create_user_email_none_raises(self):
        from models.user import UserCreate
        user = UserCreate(name="Valid Name", email="a@b.com", role="user")
        user.email = None  # bypass pydantic for direct service test
        with pytest.raises(ValidationError, match="None"):
            self.service.create_user(user)

    # --- Empty string checks ---

    def test_create_user_empty_name_raises(self):
        from models.user import UserCreate
        user = UserCreate(name="placeholder", email="a@b.com", role="user")
        user.name = ""
        with pytest.raises(ValidationError, match="empty"):
            self.service.create_user(user)

    def test_create_user_whitespace_only_name_raises(self):
        from models.user import UserCreate
        user = UserCreate(name="placeholder", email="a@b.com", role="user")
        user.name = "   "
        with pytest.raises(ValidationError, match="empty"):
            self.service.create_user(user)

    def test_create_user_empty_email_raises(self):
        from models.user import UserCreate
        user = UserCreate(name="Valid Name", email="a@b.com", role="user")
        user.email = ""
        with pytest.raises(ValidationError, match="empty"):
            self.service.create_user(user)

    def test_create_user_whitespace_only_email_raises(self):
        from models.user import UserCreate
        user = UserCreate(name="Valid Name", email="a@b.com", role="user")
        user.email = "   "
        with pytest.raises(ValidationError, match="empty"):
            self.service.create_user(user)

    # --- Excessive length checks ---

    def test_create_user_name_too_long_raises(self):
        from models.user import UserCreate
        long_name = "A" * 256
        user = UserCreate(name="placeholder", email="a@b.com", role="user")
        user.name = long_name
        with pytest.raises(ValidationError, match="255"):
            self.service.create_user(user)

    def test_create_user_email_too_long_raises(self):
        from models.user import UserCreate
        long_email = "a" * 250 + "@b.com"  # > 255 chars
        user = UserCreate(name="Valid Name", email="a@b.com", role="user")
        user.email = long_email
        with pytest.raises(ValidationError, match="255"):
            self.service.create_user(user)

    def test_create_user_name_at_max_length_succeeds(self):
        from models.user import UserCreate
        max_name = "A" * 255
        user = UserCreate(name="placeholder", email="valid@example.com", role="user")
        user.name = max_name
        result = self.service.create_user(user)
        assert result.name == max_name

    def test_create_user_email_at_max_length_succeeds(self):
        from models.user import UserCreate
        # 255 chars: 249 'a's + '@' + 'b' + '.com' = 249 + 6 = 255
        max_email = "a" * 249 + "@b.com"
        assert len(max_email) == 255
        user = UserCreate(name="Valid Name", email="a@b.com", role="user")
        user.email = max_email
        result = self.service.create_user(user)
        assert result.email == max_email

    # --- Valid input passes through ---

    def test_create_user_valid_input_succeeds(self):
        from models.user import UserCreate
        user = UserCreate(name="Jane Doe", email="jane@example.com", role="user")
        result = self.service.create_user(user)
        assert result.name == "Jane Doe"
        assert result.email == "jane@example.com"

    # --- _validate_user_input direct tests ---

    def test_validate_user_input_none_name_raises(self):
        with pytest.raises(ValidationError, match="None"):
            self.service._validate_user_input(None, "valid@example.com")

    def test_validate_user_input_none_email_raises(self):
        with pytest.raises(ValidationError, match="None"):
            self.service._validate_user_input("Valid Name", None)

    def test_validate_user_input_empty_name_raises(self):
        with pytest.raises(ValidationError, match="empty"):
            self.service._validate_user_input("", "valid@example.com")

    def test_validate_user_input_empty_email_raises(self):
        with pytest.raises(ValidationError, match="empty"):
            self.service._validate_user_input("Valid Name", "")

    def test_validate_user_input_name_too_long_raises(self):
        with pytest.raises(ValidationError, match="255"):
            self.service._validate_user_input("A" * 256, "valid@example.com")

    def test_validate_user_input_email_too_long_raises(self):
        with pytest.raises(ValidationError, match="255"):
            self.service._validate_user_input("Valid Name", "a" * 256)

    def test_validate_user_input_valid_passes(self):
        # Should not raise
        self.service._validate_user_input("Valid Name", "valid@example.com")