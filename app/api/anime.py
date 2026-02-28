from fastapi import APIRouter, Depends, status, Query, HTTPException

from app.dependencies import AnimeRepoDepends, AnimeServiceDepends, JikanDepends
from app.schemas.anime import AnimeCreate, AnimeResponse, CatalogQuery
from app.tasks.anime_tasks import sync_anime_task, sync_top_anime_task

router = APIRouter()


@router.get('/jikan/top', summary='Jikan: Топ Аниме')
async def top_anime(client: JikanDepends):
    return await client.get_top_anime(limit=5)


@router.get('/jikan/search', summary='Jikan: Поиск')
async def search_anime(query: str, client: JikanDepends):
    return await client.search_anime(query=query)


@router.get('/jikan/{mal_id}', summary='Jikan: детали по mal id')
async def get_anime_full(mal_id: int, client: JikanDepends):
    return await client.get_anime_by_id(mal_id=mal_id)


@router.post('/sync/top', status_code=status.HTTP_202_ACCEPTED)
async def queue_top_sync(limit: int = Query(25, ge=1, le=100)):
    await sync_top_anime_task.kiq(limit=limit)
    return {"message": f"синхронизация топ {limit} аниме поставлена в очередь"}


@router.post('/sync/{mal_id}', status_code=status.HTTP_202_ACCEPTED)
async def queue_anime_sync(mal_id: int):
    await sync_anime_task.kiq(mal_id)
    return {"message": f"синхронизация аниме {mal_id} поставлена в очередь"}


@router.get('/', response_model=list[AnimeResponse], summary='Каталог аниме с фильтрами')
async def get_catalog(
    repo: AnimeRepoDepends,
    query: CatalogQuery = Depends(),
):
    return await repo.get_all(query)


@router.post('/', response_model=AnimeResponse, status_code=status.HTTP_201_CREATED)
async def create_anime(anime_in: AnimeCreate, repo: AnimeRepoDepends):
    if await repo.exists_by_mal_id(anime_in.mal_id):
        return await repo.get_by_mal_id(anime_in.mal_id)
    return await repo.create(anime_in)


@router.get('/mal/{mal_id}', response_model=AnimeResponse, summary='Поиск в БД по MAL ID (или fetch из Jikan)')
async def get_anime_by_mal_id(mal_id: int, service: AnimeServiceDepends):
    return await service.get_or_fetch_by_mal_id(mal_id)


@router.get('/{anime_id}', response_model=AnimeResponse, summary='поиск по id базы данных')
async def get_anime_details(anime_id: int, repo: AnimeRepoDepends):
    anime = await repo.get_by_id(anime_id)
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'аниме не найдено в базе данных по внутреннему {anime_id}',
        )
    return anime
