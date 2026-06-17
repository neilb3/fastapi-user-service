from fastapi import HTTPException, Header
from typing import Optional

VALID_TOKENS = {
    "dev-token-123": "developer",
    "admin-token-456": "admin",
}

def verify_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    token = authorization.replace("Bearer ", "")
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Missing: token expiry check
    # Missing: token rotation enforcement
    return token

def get_token_role(token: str) -> str:
    return VALID_TOKENS.get(token, "unknown")
