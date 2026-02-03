from typing import Annotated
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.external.jikan_client import JikanClient
from app.repositories.anime_repo import AnimeRepository


def get_anime_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> AnimeRepository:
    """Фабрика репозитория аниме — каждый запрос получает свежий экземпляр с текущей сессией."""
    return AnimeRepository(session)


def get_jikan_client(request: Request) -> JikanClient:
    """Получаем Jikan клиент из app.state (инициализирован в lifespan)."""
    client = request.app.state.jikan_client
    if client is None:
        raise RuntimeError("Jikan client не инициализирован в lifespan, baka!")
    return client


# Type-алиасы для удобства (используем в роутах как AnimeRepoDepends)
AnimeRepoDepends = Annotated[AnimeRepository, Depends(get_anime_repo)]
JikanDepends = Annotated[JikanClient, Depends(get_jikan_client)]