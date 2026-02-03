from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists , delete
from sqlalchemy.engine import CursorResult
from app.models.anime import Anime, AnimeStatus, AnimeSeason
from app.schemas.anime import AnimeCreate
from typing import Optional, cast

class AnimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, anime_data: AnimeCreate) -> Anime:
        data_dict = anime_data.model_dump(exclude_unset=True)
        if 'status' in data_dict and isinstance(data_dict['status'], str):
            data_dict['status'] = AnimeStatus(data_dict['status'])
        
        if 'season' in data_dict and isinstance(data_dict['season'], str):
            data_dict['season'] = AnimeSeason(data_dict['season'])
        
        anime = Anime(**data_dict)
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