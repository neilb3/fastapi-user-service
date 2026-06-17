import os
import pytest
from datetime import datetime, timedelta, timezone

os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100")

from jose import jwt

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test-secret-key")
ALGORITHM = "HS256"


def generate_token(expires_delta: timedelta = None, expired: bool = False) -> str:
    if expired:
        expire = datetime.now(timezone.utc) - timedelta(minutes=10)
    elif expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {"sub": "testuser", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def valid_token() -> str:
    return generate_token()


@pytest.fixture
def expired_token() -> str:
    return generate_token(expired=True)


AUTH_HEADERS = {"Authorization": f"Bearer {generate_token()}"}