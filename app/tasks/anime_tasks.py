from app.database import AsyncSessionLocal
from app.external.jikan_client import JikanClient
from app.repositories.anime_repo import AnimeRepository
from app.services.anime_service import AnimeService
from app.tasks.broker import broker


@broker.task
async def sync_anime_task(mal_id: int) -> None:
    async with AsyncSessionLocal() as session:
        jikan = JikanClient()
        try:
            service = AnimeService(repo=AnimeRepository(session), jikan=jikan)
            await service.sync_from_jikan(mal_id)
        finally:
            await jikan.close()


@broker.task
async def sync_top_anime_task(limit: int = 25) -> None:
    jikan = JikanClient()
    try:
        top = await jikan.get_top_anime(limit=limit)
        for item in top:
            await sync_anime_task.kiq(item["mal_id"])
    finally:
        await jikan.close()
