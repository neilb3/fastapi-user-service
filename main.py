import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from routes import users

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    retry_after = 60  # default retry after in seconds
    response = JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded", "detail": f"Rate limit exceeded: {exc.detail}"},
        headers={"Retry-After": str(retry_after)}
    )
    return response

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(users.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
