from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.external.jikan_client import JikanClient
from app.models.user import User
from app.repositories.anime_repo import AnimeRepository
from app.repositories.user_anime_list_repo import UserAnimeListRepository
from app.repositories.user_repo import UserRepository
from app.services.anime_service import AnimeService
from app.utils.jwt import decode_token


# ─── Jikan ────────────────────────────────────────────────────────────────────

def get_jikan_client(request: Request) -> JikanClient:
    client = request.app.state.jikan_client
    if client is None:
        raise RuntimeError("Jikan client не инициализирован в lifespan")
    return client


# ─── Anime repo ───────────────────────────────────────────────────────────────

def get_anime_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> AnimeRepository:
    return AnimeRepository(session)


# ─── Redis ────────────────────────────────────────────────────────────────────

def get_redis(request: Request) -> Redis:
    redis = request.app.state.redis
    if redis is None:
        raise RuntimeError("Redis не инициализирован в lifespan")
    return redis


# ─── User repo ────────────────────────────────────────────────────────────────

def get_user_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(session)


# ─── Current user ─────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti: str = payload["jti"]
    if await redis.exists(f"blacklist:{jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user


# ─── Type aliases ─────────────────────────────────────────────────────────────

def get_user_anime_list_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserAnimeListRepository:
    return UserAnimeListRepository(session)


def get_anime_service(
    repo: Annotated[AnimeRepository, Depends(get_anime_repo)],
    jikan: Annotated[JikanClient, Depends(get_jikan_client)],
) -> AnimeService:
    return AnimeService(repo=repo, jikan=jikan)


AnimeRepoDepends = Annotated[AnimeRepository, Depends(get_anime_repo)]
JikanDepends = Annotated[JikanClient, Depends(get_jikan_client)]
UserRepoDepends = Annotated[UserRepository, Depends(get_user_repo)]
RedisDependency = Annotated[Redis, Depends(get_redis)]
CurrentUser = Annotated[User, Depends(get_current_user)]
UserAnimeListRepoDepends = Annotated[UserAnimeListRepository, Depends(get_user_anime_list_repo)]
AnimeServiceDepends = Annotated[AnimeService, Depends(get_anime_service)]
