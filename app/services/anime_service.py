import httpx
from fastapi import HTTPException, status as http_status

from app.external.jikan_client import JikanClient
from app.models.anime import Anime, AnimeStatus, AnimeSeason
from app.repositories.anime_repo import AnimeRepository, GenreInput
from app.schemas.anime import AnimeCreate, AnimeUpdate

_STATUS_MAP = {
    "Finished Airing": AnimeStatus.FINISHED,
    "Currently Airing": AnimeStatus.AIRING,
    "Not yet aired": AnimeStatus.UPCOMING,
}


class AnimeService:
    def __init__(self, repo: AnimeRepository, jikan: JikanClient):
        self.repo = repo
        self.jikan = jikan

    async def get_or_fetch_by_mal_id(self, mal_id: int) -> Anime:
        anime = await self.repo.get_by_mal_id(mal_id)
        if anime:
            return anime
        data = await self._fetch_from_jikan(mal_id)
        return await self._save_from_jikan(data)

    async def sync_from_jikan(self, mal_id: int) -> Anime:
        data = await self._fetch_from_jikan(mal_id)
        return await self._save_from_jikan(data)

    async def _fetch_from_jikan(self, mal_id: int) -> dict:
        try:
            return await self.jikan.get_anime_by_id(mal_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Аниме {mal_id} не найдено на MAL",
                )
            raise HTTPException(
                status_code=http_status.HTTP_502_BAD_GATEWAY,
                detail="Ошибка Jikan API",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=http_status.HTTP_502_BAD_GATEWAY,
                detail="Jikan недоступен",
            )

    async def _save_from_jikan(self, data: dict) -> Anime:
        mal_id = data["mal_id"]
        anime_data = self._parse(data)
        genres = self._extract_genres(data)

        existing = await self.repo.get_by_mal_id(mal_id)  # 1 query instead of exists+get
        if existing:
            update_data = AnimeUpdate(**anime_data.model_dump(exclude={"mal_id"}))
            anime = await self.repo.update(existing.id, update_data)  # use RETURNING result
        else:
            anime = await self.repo.create(anime_data)

        anime = await self.repo.sync_genres(anime.id, genres)  # always sync, even if empty
        return anime

    def _parse(self, data: dict) -> AnimeCreate:
        status_str = data.get("status")
        season_str = data.get("season")
        return AnimeCreate(
            mal_id=data["mal_id"],
            title=data["title"],
            title_english=data.get("title_english"),
            title_japanese=data.get("title_japanese"),
            synopsis=data.get("synopsis"),
            score=data.get("score"),
            episodes=data.get("episodes"),
            status=_STATUS_MAP.get(status_str) if status_str else None,
            season=AnimeSeason(season_str) if season_str and season_str in AnimeSeason._value2member_map_ else None,
            year=data.get("year"),
            image_url=data.get("images", {}).get("jpg", {}).get("image_url"),
        )

    def _extract_genres(self, data: dict) -> list[GenreInput]:
        genres: list[GenreInput] = []
        for g in data.get("genres", []) + data.get("themes", []):
            genres.append({"name": g["name"], "mal_id": g["mal_id"]})
        return genres
