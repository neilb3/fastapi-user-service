import pytest
import os
from fastapi.testclient import TestClient
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API_TOKENS env var before importing app
# This is how tokens are loaded in production - via environment, not hardcode
os.environ["API_TOKENS"] = "dev-token-123:developer,admin-token-456:admin"
os.environ["TOKEN_EXPIRY_SECONDS"] = "86400"

from main import app
from slowapi import Limiter
from slowapi.util import get_remote_address

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-token-123"}

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

def test_get_users_rate_limit_returns_429():
    """Verify that exceeding the rate limit returns HTTP 429."""
    from unittest.mock import patch, MagicMock
    from slowapi.errors import RateLimitExceeded
    import limits

    # Simulate a rate limit exceeded error by patching the limiter's check
    with patch("routes.users.limiter._check_request_limit") as mock_check:
        mock_check.side_effect = RateLimitExceeded(
            limit=MagicMock(limit=MagicMock(__str__=lambda self: "100 per 1 minute"))
        )
        response = client.get("/api/users", headers=AUTH_HEADERS)
    assert response.status_code == 429

def test_get_users_rate_limit_retry_after_header():
    """Verify that the 429 response includes a Retry-After header."""
    from unittest.mock import patch, MagicMock
    from slowapi.errors import RateLimitExceeded

    with patch("routes.users.limiter._check_request_limit") as mock_check:
        mock_check.side_effect = RateLimitExceeded(
            limit=MagicMock(limit=MagicMock(__str__=lambda self: "100 per 1 minute"))
        )
        response = client.get("/api/users", headers=AUTH_HEADERS)
    assert response.status_code == 429
    assert "retry-after" in response.headers or "Retry-After" in response.headers
