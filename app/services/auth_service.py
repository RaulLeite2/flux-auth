from fastapi import HTTPException, status
from jose import JWTError, jwt
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session, redis_client: Redis) -> None:
        self.db = db
        self.redis = redis_client
        self.repo = UserRepository(db)

    def register(self, payload: RegisterRequest) -> TokenResponse:
        if self.repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        if self.repo.get_by_username(payload.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already in use")

        user = self.repo.create(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )

        return self._issue_tokens(str(user.id))

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        return self._issue_tokens(str(user.id))

    def refresh(self, refresh_token: str) -> TokenResponse:
        if self.redis.get(f"revoked:{refresh_token}"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

        try:
            payload = jwt.decode(refresh_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        self.revoke(refresh_token)
        return self._issue_tokens(payload["sub"])

    def revoke(self, refresh_token: str) -> None:
        self.redis.setex(f"revoked:{refresh_token}", 60 * 60 * 24 * settings.refresh_token_expire_days, "1")

    def _issue_tokens(self, user_id: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
