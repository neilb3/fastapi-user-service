import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app
from services.user_service import SentimentScorer

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


# SentimentScorer tests

def test_sentiment_scorer_raises_type_error_for_none():
    scorer = SentimentScorer()
    with pytest.raises(TypeError, match="text must be a string"):
        scorer.score(None)


def test_sentiment_scorer_raises_type_error_for_non_string():
    scorer = SentimentScorer()
    with pytest.raises(TypeError, match="text must be a string"):
        scorer.score(12345)


def test_sentiment_scorer_raises_value_error_for_empty_string():
    scorer = SentimentScorer()
    with pytest.raises(ValueError, match="empty or whitespace-only"):
        scorer.score("")


def test_sentiment_scorer_raises_value_error_for_whitespace_only():
    scorer = SentimentScorer()
    with pytest.raises(ValueError, match="empty or whitespace-only"):
        scorer.score("   \t\n  ")


def test_sentiment_scorer_raises_value_error_for_text_too_long():
    scorer = SentimentScorer()
    with pytest.raises(ValueError, match="must not exceed 5000 characters"):
        scorer.score("a" * 5001)


def test_sentiment_scorer_returns_neutral_for_valid_text():
    scorer = SentimentScorer()
    result = scorer.score("This is a valid sentence.")
    assert result == "neutral"


def test_sentiment_scorer_accepts_text_at_max_length():
    scorer = SentimentScorer()
    result = scorer.score("a" * 5000)
    assert result == "neutral"