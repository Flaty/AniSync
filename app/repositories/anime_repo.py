from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists , delete
from sqlalchemy.engine import CursorResult
from app.models.anime import Anime, AnimeStatus, AnimeSeason
from typing import Optional, cast

class AnimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, anime_data: dict) -> Anime:
        if 'status' in anime_data and isinstance(anime_data['status'], str):
            anime_data['status'] = AnimeStatus(anime_data['status'])
        
        if 'season' in anime_data and isinstance(anime_data['season'], str):
            anime_data['season'] = AnimeSeason(anime_data['season'])
        
        anime = Anime(**anime_data)
        self.session.add(anime)
        await self.session.commit()
        await self.session.refresh(anime)
        return anime
    
    async def get_by_id(self, anime_id: int) -> Optional[Anime]:
        stmt = select(Anime).where(Anime.id == anime_id)
        result = await self.session.scalars(stmt)
        return result.one_or_none()
    
    async def get_by_mal_id(self, mal_id: int) -> Optional[Anime]:
        stmt = select(Anime).where(Anime.mal_id == mal_id)
        result = await self.session.scalars(stmt)
        return result.one_or_none()
    
    async def get_all(
            self,
            limit: int = 10,
            offset: int = 0,
            min_score: Optional[float] = None
    ) -> list[Anime]:
        
        stmt = select(Anime)

        if min_score is not None:
            stmt = stmt.where(Anime.score >= min_score)
        
        stmt = stmt.order_by(Anime.score.desc()).limit(limit).offset(offset)

        result = await self.session.scalars(stmt)
        return list(result.all())
    
    async def update(self, anime_id: int, update_data: dict) -> Optional[Anime]:

        stmt = (
            update(Anime)
            .where(Anime.id == anime_id)
            .values(**update_data)
            .returning(Anime)
        )

        result = await self.session.scalars(stmt)
        await self.session.commit()
        return result.one_or_none()
    
    async def delete(self, anime_id: int) -> bool:

        stmt = delete(Anime).where(Anime.id == anime_id).execution_options(synchronize_session=False)

        result = await self.session.execute(stmt)
        await self.session.commit()
        cursor_result = cast(CursorResult[None], result)
        return cursor_result.rowcount > 0
    
    async def exists_by_mal_id(self, mal_id: int) -> bool:

        stmt = select(exists().where(Anime.mal_id == mal_id))
        result = await self.session.execute(stmt)
        return cast(bool, result.scalar())