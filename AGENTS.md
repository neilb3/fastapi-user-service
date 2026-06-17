# AGENTS.md

## Project Overview
fastapi-user-service is an internal REST API for user management built with FastAPI.

## File Ownership
| File | Domain |
|------|--------|
| routes/users.py | All /api/users endpoints |
| services/user_service.py | Business logic, no HTTP |
| models/user.py | Pydantic schemas |
| utils/auth.py | Token verification |
| tests/test_users.py | All user endpoint tests |

## Adding Rate Limiting
Use the slowapi library (already in requirements.txt):
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

Apply with @limiter.limit("100/minute") on routes.
The app needs a state.limiter and an exception handler for 429s.

## Testing
- Auth header: {"Authorization": "Bearer dev-token-123"}
- Rate limit tests: verify 429 after limit exceeded
- Use TestClient from fastapi.testclient

## Security Rules
- Never commit .env files
- All /api/ endpoints require verify_token dependency
