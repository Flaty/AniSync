from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.config import settings
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.utils.security import verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository, redis: Redis):
        self.user_repo = user_repo
        self.redis = redis

    async def register(self, data: RegisterRequest) -> TokenResponse:
        if await self.user_repo.exists_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = await self.user_repo.create(data)
        return await self._issue_tokens(user.id)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        return await self._issue_tokens(user.id)

    async def logout(self, access_token: str, user_id: int) -> None:
        payload = decode_token(access_token)
        jti: str = payload["jti"]
        exp: int = payload["exp"]

        now_ts = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - now_ts
        if ttl > 0:
            await self.redis.setex(f"blacklist:{jti}", ttl, "1")

        await self.redis.delete(f"refresh_token:{user_id}")

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = int(payload["sub"])
        stored = await self.redis.get(f"refresh_token:{user_id}")

        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found, please login again",
                headers={"WWW-Authenticate": "Bearer"},
            )

        stored_str = stored.decode() if isinstance(stored, bytes) else stored
        if stored_str != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token mismatch, please login again",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await self._issue_tokens(user_id)

    async def _issue_tokens(self, user_id: int) -> TokenResponse:
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        refresh_ttl = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())
        await self.redis.setex(f"refresh_token:{user_id}", refresh_ttl, refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
