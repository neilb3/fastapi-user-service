from fastapi import APIRouter, HTTPException, Depends
from models.user import UserCreate, UserResponse
from services.user_service import UserService
from utils.auth import verify_token

router = APIRouter()
user_service = UserService()

# NOTE: No rate limiting on this endpoint - high volume requests
# are causing performance degradation (see PROJ-42)
@router.get("/users", response_model=list[UserResponse])
def get_users(token: str = Depends(verify_token)):
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
