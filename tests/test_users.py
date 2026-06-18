import pytest
import os

# Set environment before importing app
os.environ["API_TOKENS"] = "dev-token-123:developer,admin-token-456:admin"
os.environ["TOKEN_EXPIRY_SECONDS"] = "86400"
os.environ["RATE_LIMIT_PER_MINUTE"] = "3"  # Low limit so tests can trigger it easily

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from fastapi.testclient import TestClient

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
    # Rate limit is set to 3/minute in test env
    # Make 4 real requests - the 4th should be blocked
    with TestClient(app) as c:
        for _ in range(3):
            c.get("/api/users", headers=AUTH_HEADERS)
        response = c.get("/api/users", headers=AUTH_HEADERS)
    assert response.status_code == 429


def test_get_users_rate_limit_has_retry_after_header():
    # Make enough requests to trigger the limit then check headers
    with TestClient(app) as c:
        for _ in range(3):
            c.get("/api/users", headers=AUTH_HEADERS)
        response = c.get("/api/users", headers=AUTH_HEADERS)
    assert response.status_code == 429
    header_keys = {k.lower() for k in response.headers.keys()}
    assert "retry-after" in header_keys


def test_get_user_by_id_rate_limit_returns_429():
    with TestClient(app) as c:
        for _ in range(3):
            c.get("/api/users/1", headers=AUTH_HEADERS)
        response = c.get("/api/users/1", headers=AUTH_HEADERS)
    assert response.status_code == 429


def test_get_user_by_id_rate_limit_has_retry_after_header():
    with TestClient(app) as c:
        for _ in range(3):
            c.get("/api/users/1", headers=AUTH_HEADERS)
        response = c.get("/api/users/1", headers=AUTH_HEADERS)
    assert response.status_code == 429
    header_keys = {k.lower() for k in response.headers.keys()}
    assert "retry-after" in header_keys


def test_create_user_rate_limit_returns_429():
    payload = {"name": "Rate Limit User", "email": "ratelimit@example.com", "role": "user"}
    with TestClient(app) as c:
        for _ in range(3):
            c.post("/api/users", json=payload, headers=AUTH_HEADERS)
        response = c.post("/api/users", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 429


def test_create_user_rate_limit_has_retry_after_header():
    payload = {"name": "Rate Limit User", "email": "ratelimit2@example.com", "role": "user"}
    with TestClient(app) as c:
        for _ in range(3):
            c.post("/api/users", json=payload, headers=AUTH_HEADERS)
        response = c.post("/api/users", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 429
    header_keys = {k.lower() for k in response.headers.keys()}
    assert "retry-after" in header_keys