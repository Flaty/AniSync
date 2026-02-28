from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists, delete, insert, func, or_
from sqlalchemy.engine import CursorResult
from app.models.anime import Anime
from app.models.genre import Genre, anime_genres
from app.schemas.anime import AnimeCreate, AnimeUpdate, CatalogQuery
from app.repositories.genre_repo import GenreRepository
from typing import Optional, cast, TypedDict

class GenreInput(TypedDict):
    name: str
    mal_id: Optional[int]

class AnimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.genre_repo = GenreRepository(session)
    
    async def create(self, anime_data: AnimeCreate) -> Anime:
        data_dict = anime_data.model_dump(exclude_unset=True)
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
    
    async def get_all(self, query: CatalogQuery) -> list[Anime]:
        stmt = select(Anime)

        if query.genre:
            genre_subq = (
                select(anime_genres.c.anime_id)
                .join(Genre, Genre.id == anime_genres.c.genre_id)
                .where(Genre.name.ilike(f"%{query.genre}%"))
                .scalar_subquery()
            )
            stmt = stmt.where(Anime.id.in_(genre_subq))

        if query.status is not None:
            stmt = stmt.where(Anime.status == query.status)

        if query.season is not None:
            stmt = stmt.where(Anime.season == query.season)

        if query.year is not None:
            stmt = stmt.where(Anime.year == query.year)

        if query.min_score is not None:
            stmt = stmt.where(Anime.score >= query.min_score)

        if query.search:
            pattern = f"%{query.search}%"
            stmt = stmt.where(
                or_(
                    Anime.title.ilike(pattern),
                    Anime.title_english.ilike(pattern),
                )
            )

        stmt = stmt.order_by(Anime.score.desc().nulls_last()).limit(query.limit).offset(query.offset)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_recommendations(self, user_id: int, limit: int = 10) -> list[Anime]:
        from app.models.user_anime_list import UserAnimeList

        top_genre_ids = (
            select(anime_genres.c.genre_id)
            .join(UserAnimeList, UserAnimeList.anime_id == anime_genres.c.anime_id)
            .where(UserAnimeList.user_id == user_id)
            .group_by(anime_genres.c.genre_id)
            .order_by(func.count().desc())
            .limit(5)
        )

        in_list = (
            select(UserAnimeList.anime_id)
            .where(UserAnimeList.user_id == user_id)
        )

        stmt = (
            select(Anime)
            .join(anime_genres, anime_genres.c.anime_id == Anime.id)
            .where(
                anime_genres.c.genre_id.in_(top_genre_ids),
                Anime.id.notin_(in_list),
            )
            .distinct()
            .order_by(Anime.score.desc().nulls_last())
            .limit(limit)
        )

        result = await self.session.scalars(stmt)
        return list(result.all())
    
    async def update(self, anime_id: int, update_data: AnimeUpdate) -> Optional[Anime]:
        values = update_data.model_dump(exclude_unset=True)

        if not values:
            return await self.get_by_id(anime_id)

        stmt = (
            update(Anime)
            .where(Anime.id == anime_id)
            .values(**values)
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

    async def exists_by_id(self, anime_id: int) -> bool:

        stmt = select(exists().where(Anime.id == anime_id))
        result = await self.session.execute(stmt)
        return cast(bool, result.scalar())
    
    async def sync_genres(self, anime_id: int, genres_input: list[GenreInput]) -> Optional[Anime]:
        anime = await self.get_by_id(anime_id)  
        if not anime:
            return None
        
        new_genre_ids = set()
        for g in genres_input:
            genre = await self.genre_repo.upsert(
                name=g['name'],
                mal_id=g.get('mal_id')
            )
            new_genre_ids.add(genre.id)
        
        # Атомарный sync
        await self.session.execute(
            delete(anime_genres).where(anime_genres.c.anime_id == anime_id)
        )

        if new_genre_ids:
            values = [{'anime_id': anime_id, 'genre_id': gid} for gid in new_genre_ids]
            await self.session.execute(insert(anime_genres), values)

        await self.session.commit()
        await self.session.refresh(anime, attribute_names=['genres']) 

        return anime
