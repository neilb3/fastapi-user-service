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


# ---------------------------------------------------------------------------
# SentimentScorer.score() validation tests
# ---------------------------------------------------------------------------

class TestSentimentScorerValidation:
    def setup_method(self):
        self.scorer = SentimentScorer()

    def test_score_raises_type_error_for_none(self):
        with pytest.raises(TypeError, match="text must be a string"):
            self.scorer.score(None)

    def test_score_raises_type_error_for_non_string(self):
        with pytest.raises(TypeError, match="text must be a string"):
            self.scorer.score(12345)

    def test_score_raises_type_error_for_list(self):
        with pytest.raises(TypeError, match="text must be a string"):
            self.scorer.score(["hello"])

    def test_score_raises_value_error_for_empty_string(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            self.scorer.score("")

    def test_score_raises_value_error_for_whitespace_only(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            self.scorer.score("   ")

    def test_score_raises_value_error_for_newline_only(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            self.scorer.score("\n\t  ")

    def test_score_raises_value_error_for_text_exceeding_max_length(self):
        long_text = "a" * 5001
        with pytest.raises(ValueError, match="5000 characters"):
            self.scorer.score(long_text)

    def test_score_raises_value_error_for_text_exactly_one_over_max(self):
        long_text = "x" * 5001
        with pytest.raises(ValueError, match="5000 characters"):
            self.scorer.score(long_text)

    def test_score_accepts_text_at_max_length(self):
        text = "good " * 1000  # 5000 chars exactly
        result = self.scorer.score(text)
        assert result in ("positive", "negative", "neutral")

    def test_score_returns_string_for_valid_input(self):
        result = self.scorer.score("This is a normal sentence.")
        assert isinstance(result, str)

    def test_score_positive_sentiment(self):
        result = self.scorer.score("This is great!")
        assert result == "positive"

    def test_score_negative_sentiment(self):
        result = self.scorer.score("This is terrible.")
        assert result == "negative"

    def test_score_neutral_sentiment(self):
        result = self.scorer.score("The sky is blue.")
        assert result == "neutral"