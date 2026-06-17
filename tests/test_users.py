import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API_TOKENS env var before importing app
# This is how tokens are loaded in production - via environment, not hardcode
os.environ["API_TOKENS"] = "dev-token-123:developer,admin-token-456:admin"
os.environ["TOKEN_EXPIRY_SECONDS"] = "86400"

from main import app

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

def _make_rate_limit_exceeded():
    """Create a RateLimitExceeded exception with a proper mock limit object."""
    from slowapi.errors import RateLimitExceeded
    mock_limit = MagicMock()
    mock_limit.error_message = None
    mock_limit.__str__ = lambda self: "100 per 1 minute"
    exc = RateLimitExceeded(mock_limit)
    exc.retry_after = 60
    return exc

def test_get_users_rate_limit_returns_429():
    """Test that exceeding the rate limit returns HTTP 429 with Retry-After header."""
    from utils.auth import limiter

    original_check = limiter._check_request_limit

    call_count = {"count": 0}

    def mock_check(request, endpoint_func, limit_provider, *args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] > 1:
            raise _make_rate_limit_exceeded()
        return original_check(request, endpoint_func, limit_provider, *args, **kwargs)

    with patch.object(limiter, "_check_request_limit", side_effect=mock_check):
        # First request should succeed
        response = client.get("/api/users", headers=AUTH_HEADERS)
        assert response.status_code == 200

        # Second request should be rate limited
        response = client.get("/api/users", headers=AUTH_HEADERS)
        assert response.status_code == 429
        assert "Retry-After" in response.headers

def test_get_users_rate_limit_retry_after_header():
    """Test that the 429 response includes a Retry-After header."""
    from utils.auth import limiter

    def mock_check(request, endpoint_func, limit_provider, *args, **kwargs):
        raise _make_rate_limit_exceeded()

    with patch.object(limiter, "_check_request_limit", side_effect=mock_check):
        response = client.get("/api/users", headers=AUTH_HEADERS)
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert int(response.headers["Retry-After"]) > 0
