from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routes.users import router as users_router
import os

# Rate limit is configurable via env var
# Production default: 100/minute. Tests use: 3/minute
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "100")

limiter = Limiter(key_func=get_remote_address, default_limits=[])
app = FastAPI(title="User Service API", version="1.0.0")
app.state.limiter = limiter
app.state.rate_limit = RATE_LIMIT

async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded", "detail": str(exc)},
        headers={"Retry-After": "60"}
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
app.include_router(users_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}