from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from routes.users import router as users_router
from utils.auth import limiter

app = FastAPI(
    title="User Service API",
    description="Internal user management service",
    version="1.0.0"
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={"detail": "Too Many Requests"},
        headers={"Retry-After": str(retry_after)}
    )

app.include_router(users_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
