import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
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


def test_get_users_rate_limit_returns_429():
    with TestClient(app) as c:
        for _ in range(3):
            c.get("/api/users", headers=AUTH_HEADERS)
        response = c.get("/api/users", headers=AUTH_HEADERS)
    assert response.status_code == 429


def test_get_users_rate_limit_has_retry_after_header():
    with TestClient(app) as c:
        for _ in range(3):
            c.get("/api/users", headers=AUTH_HEADERS)
        response = c.get("/api/users", headers=AUTH_HEADERS)
    assert response.status_code == 429
    assert "retry-after" in {k.lower() for k in response.headers.keys()}