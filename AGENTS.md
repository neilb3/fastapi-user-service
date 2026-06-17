# AGENTS.md

## Project Overview
fastapi-user-service is an internal REST API for user management built with FastAPI.

## File Ownership
| File | Domain |
|------|--------|
| routes/users.py | All /api/users endpoints |
| services/user_service.py | Business logic, no HTTP |
| models/user.py | Pydantic schemas |
| utils/auth.py | Token verification and expiry |
| utils/rate_limit.py | Rate limiter setup |
| tests/test_users.py | All user endpoint tests |

## Adding Rate Limiting
Use slowapi (already in requirements.txt). Add to main.py:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Add to routes/users.py:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@router.get("/users", response_model=list[UserResponse])
@limiter.limit("100/minute")
def get_users(request: Request, token: str = Depends(verify_token)):
    return user_service.get_all_users()
```

NOTE: The route function MUST have `request: Request` as first parameter for slowapi to work.

## Rate Limit Testing - EXACT PATTERN TO USE
IMPORTANT: Always use this exact pattern for rate limit tests. Do not invent alternatives.

```python
from unittest.mock import patch
from slowapi.errors import RateLimitExceeded

def test_get_users_rate_limit_returns_429():
    def mock_check(request, endpoint, limit_provider):
        raise RateLimitExceeded("100 per 1 minute")
    with patch.object(app.state.limiter, "_check_request_limit", side_effect=mock_check):
        response = client.get("/api/users", headers=AUTH_HEADERS)
        assert response.status_code == 429

def test_get_users_rate_limit_has_retry_after_header():
    def mock_check(request, endpoint, limit_provider):
        raise RateLimitExceeded("100 per 1 minute")
    with patch.object(app.state.limiter, "_check_request_limit", side_effect=mock_check):
        response = client.get("/api/users", headers=AUTH_HEADERS)
        assert response.status_code == 429
        assert "Retry-After" in response.headers or "retry-after" in response.headers
```

The mock_check function MUST have exactly these three arguments: request, endpoint, limit_provider.

## Testing Setup
- Auth header: {"Authorization": "Bearer dev-token-123"}
- Set env before importing app: os.environ["API_TOKENS"] = "dev-token-123:developer,admin-token-456:admin"
- Use TestClient from fastapi.testclient
- Import app AFTER setting os.environ

## Security Rules
- Never commit .env files
- All /api/ endpoints require verify_token dependency
- Tokens must come from environment variables, never hardcoded in source
