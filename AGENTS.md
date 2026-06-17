# AGENTS.md

## Project Overview
fastapi-user-service is an internal REST API for user management built with FastAPI.

## File Ownership
| File | Domain | Locked |
|------|--------|--------|
| routes/users.py | All /api/users endpoints | No |
| services/user_service.py | Business logic, no HTTP | No |
| models/user.py | Pydantic schemas | No |
| utils/auth.py | Token verification and expiry | YES - DO NOT MODIFY |
| tests/test_users.py | All user endpoint tests | No |
| main.py | App entry point, rate limit handler | No |

## CRITICAL: utils/auth.py IS LOCKED
DO NOT modify utils/auth.py under any circumstances.
It already implements:
- Token loading from API_TOKENS environment variable (not hardcoded)
- Token expiry enforcement via TOKEN_EXPIRY_SECONDS environment variable
- Proper Bearer token parsing

Any changes to auth.py will be rejected. If auth changes are needed, raise a separate ticket.

## Rate Limiting - CRITICAL RULES

### Environment Variable
Rate limit is controlled by RATE_LIMIT_PER_MINUTE env var.
- Production default: 100
- Test environment: 3 (set in tests/test_users.py)

### main.py pattern - always use this exactly
```python
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "100")
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="User Service API", version="1.0.0")
app.state.limiter = limiter

async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded"},
        headers={"Retry-After": "60"}
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
```

NEVER use _rate_limit_exceeded_handler from slowapi. It breaks in tests.

### routes/users.py pattern
```python
from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

limiter = Limiter(key_func=get_remote_address)

@router.get("/users", response_model=list[UserResponse])
@limiter.limit(lambda: os.getenv("RATE_LIMIT_PER_MINUTE", "100") + "/minute")
def get_users(request: Request, token: str = Depends(verify_token)):
    return user_service.get_all_users()
```

request: Request MUST be first parameter in rate-limited routes.

## Rate Limit Testing - EXACT PATTERN
No mocking. Make real requests. Rate limit is 3/minute in tests.

```python
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
```

## Test Setup
```python
import os
os.environ["API_TOKENS"] = "dev-token-123:developer,admin-token-456:admin"
os.environ["TOKEN_EXPIRY_SECONDS"] = "86400"
os.environ["RATE_LIMIT_PER_MINUTE"] = "3"
from main import app
from fastapi.testclient import TestClient
client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-token-123"}
```

## Security Rules
- Never commit .env files
- All /api/ endpoints require verify_token dependency
- utils/auth.py is LOCKED - do not modify it
- Tokens must come from environment variables only
