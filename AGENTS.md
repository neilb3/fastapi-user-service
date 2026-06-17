# AGENTS.md

## Project Overview
fastapi-user-service is an internal REST API for user management built with FastAPI.

## File Ownership
| File | Domain | Notes |
|------|--------|-------|
| routes/users.py | All /api/users endpoints | Rate limiting here |
| services/user_service.py | Business logic | No HTTP logic |
| models/user.py | Pydantic schemas | |
| utils/auth.py | Authentication | Rewrite with JWT for PROJ-44 |
| tests/test_users.py | Tests | Use conftest.py for env setup |
| tests/conftest.py | Test config | Sets env vars before app import |
| main.py | App entry point | Custom rate limit handler |

## JWT Authentication (PROJ-44)
Replace static token lookup with JWT using python-jose.

### utils/auth.py - JWT pattern
```python
from fastapi import HTTPException, Header
from typing import Optional
from jose import jwt, JWTError
import os, time

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"

def generate_token(role: str = "developer", expires_in: int = 86400) -> str:
    payload = {
        "role": role,
        "exp": time.time() + expires_in,
        "iat": time.time(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role", "unknown")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

### tests/conftest.py - JWT pattern
```python
import pytest, os
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["RATE_LIMIT_PER_MINUTE"] = "3"

from utils.auth import generate_token

@pytest.fixture(scope="session")
def auth_headers():
    token = generate_token(role="developer")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="session")  
def expired_headers():
    token = generate_token(role="developer", expires_in=-1)
    return {"Authorization": f"Bearer {token}"}
```

### tests/test_users.py - JWT pattern
```python
def test_get_users_success(auth_headers):
    response = client.get("/api/users", headers=auth_headers)
    assert response.status_code == 200

def test_expired_token_returns_401(expired_headers):
    response = client.get("/api/users", headers=expired_headers)
    assert response.status_code == 401
```

## Rate Limiting Rules
- Use RATE_LIMIT_PER_MINUTE env var (default 100, tests use 3)
- Use custom_rate_limit_handler - NEVER use _rate_limit_exceeded_handler
- request: Request MUST be first parameter in rate-limited routes

## Rate Limit Test Pattern
```python
def test_get_users_rate_limit_returns_429(auth_headers):
    with TestClient(app) as c:
        for _ in range(3):
            c.get("/api/users", headers=auth_headers)
        response = c.get("/api/users", headers=auth_headers)
    assert response.status_code == 429
```

## Security Rules
- Never commit .env files
- All /api/ endpoints require verify_token dependency
- JWT_SECRET_KEY must come from environment variable
- Test secrets go in conftest.py only
