from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.genre import Genre
from typing import Optional

class GenreRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, name: str) -> Genre:
        normalized_name = name.strip().lower()

        stmt = select(Genre).where(Genre.name == normalized_name)
        result = await self.session.scalars(stmt)
        genre = result.one_or_none()

        if genre:
            return genre
        
        genre = Genre(name=normalized_name)
        self.session.add(genre)
        await self.session.flush()
        return genre
    
    async def get_by_name(self, name: str) -> Optional[Genre]:
        normalized_name = name.strip().lower()
        stmt = select(Genre).where(Genre.name == normalized_name)
        result = await self.session.scalars(stmt)
        return result.one_or_none()
    
    async def get_all(self) -> list[Genre]:
        stmt = select(Genre).order_by(Genre.name)
        result = await self.session.scalars(stmt)
        return list(result.all())
    
    async def get_by_ids(self, genre_id: list[int]) -> list[Genre]:
        stmt = select(Genre).where(Genre.id.in_(genre_id))
        result = await self.session.scalars(stmt)
        return list(result.all())