from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from app.services.auth_service import register_user, login_user
from app.core.dependencies import get_current_user
from app.core.rate_limit import limit_auth, limit_login_email
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse, dependencies=[Depends(limit_auth)])
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(data, db)

@router.post("/login", response_model=AuthResponse, dependencies=[Depends(limit_auth)])
def login(data: LoginRequest, db: Session = Depends(get_db)):
    limit_login_email(data.email)
    return login_user(data, db)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
