from fastapi import APIRouter, Depends, status
from redis import Redis
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService
from app.utils.redis_client import get_redis

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    return AuthService(db, redis).register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    return AuthService(db, redis).login(payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    return AuthService(db, redis).refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    AuthService(db, redis).revoke(payload.refresh_token)
    return None
