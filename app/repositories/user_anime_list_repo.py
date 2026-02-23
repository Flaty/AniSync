from typing import Optional

from sqlalchemy import select, update, delete, exists
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_anime_list import UserAnimeList, WatchStatus
from app.schemas.user_anime_list import UserAnimeListCreate, UserAnimeListUpdate


class UserAnimeListRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, data: UserAnimeListCreate) -> UserAnimeList:
        entry = UserAnimeList(
            user_id=user_id,
            anime_id=data.anime_id,
            status=data.status,
            score=data.score,
            progress=data.progress,
        )
        self.session.add(entry)
        await self.session.commit()
        return await self.get_by_user_and_anime(user_id, data.anime_id)

    async def get_by_user(
        self,
        user_id: int,
        status: Optional[WatchStatus] = None,
    ) -> list[UserAnimeList]:
        stmt = select(UserAnimeList).where(UserAnimeList.user_id == user_id)
        if status is not None:
            stmt = stmt.where(UserAnimeList.status == status)
        stmt = stmt.order_by(UserAnimeList.created_at.desc())
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_user_and_anime(
        self, user_id: int, anime_id: int
    ) -> Optional[UserAnimeList]:
        stmt = select(UserAnimeList).where(
            UserAnimeList.user_id == user_id,
            UserAnimeList.anime_id == anime_id,
        )
        result = await self.session.scalars(stmt)
        return result.one_or_none()

    async def update(
        self, user_id: int, anime_id: int, data: UserAnimeListUpdate
    ) -> Optional[UserAnimeList]:
        values = data.model_dump(exclude_none=True)
        stmt = (
            update(UserAnimeList)
            .where(
                UserAnimeList.user_id == user_id,
                UserAnimeList.anime_id == anime_id,
            )
            .values(**values)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            return None
        await self.session.commit()
        return await self.get_by_user_and_anime(user_id, anime_id)

    async def delete(self, user_id: int, anime_id: int) -> bool:
        stmt = (
            delete(UserAnimeList)
            .where(
                UserAnimeList.user_id == user_id,
                UserAnimeList.anime_id == anime_id,
            )
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, user_id: int, anime_id: int) -> bool:
        stmt = select(
            exists().where(
                UserAnimeList.user_id == user_id,
                UserAnimeList.anime_id == anime_id,
            )
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar())
