import os
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from models.user import UserCreate, UserResponse
from services.user_service import UserService
from utils.auth import verify_token

router = APIRouter()
user_service = UserService()
limiter = Limiter(key_func=get_remote_address)

@router.get("/users", response_model=list[UserResponse])
@limiter.limit(lambda: os.getenv("RATE_LIMIT_PER_MINUTE", "100") + "/minute")
def get_users(request: Request, token: str = Depends(verify_token)):
    return user_service.get_all_users()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, token: str = Depends(verify_token)):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, token: str = Depends(verify_token)):
    return user_service.create_user(user)