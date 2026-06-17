from fastapi import HTTPException, Header, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import os
import time

# Tokens loaded from environment variables - never hardcoded in source code
# Set API_TOKENS in your .env file as: token1:role1,token2:role2
_raw = os.getenv("API_TOKENS", "")
VALID_TOKENS: dict[str, str] = {}
if _raw:
    for pair in _raw.split(","):
        if ":" in pair:
            token, role = pair.strip().split(":", 1)
            VALID_TOKENS[token.strip()] = role.strip()

# Token expiry enforcement (default 24 hours)
TOKEN_EXPIRY_SECONDS = int(os.getenv("TOKEN_EXPIRY_SECONDS", "86400"))
_token_first_seen: dict[str, float] = {}

# Rate limiter instance - use remote address as the key
limiter = Limiter(key_func=get_remote_address)

def verify_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    token = authorization.split(" ", 1)[1]
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Token expiry check
    now = time.time()
    if token not in _token_first_seen:
        _token_first_seen[token] = now
    if now - _token_first_seen[token] > TOKEN_EXPIRY_SECONDS:
        raise HTTPException(status_code=401, detail="Token expired")
    return token

def get_token_role(token: str) -> str:
    return VALID_TOKENS.get(token, "unknown")
