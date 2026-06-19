from fastapi import FastAPI
from routes.users import router as users_router

app = FastAPI(title="User Service API", version="1.0.0")
app.include_router(users_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
