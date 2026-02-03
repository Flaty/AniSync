from fastapi import APIRouter, status, Query, HTTPException
from app.dependencies import AnimeRepoDepends, JikanDepends
from app.schemas.anime import AnimeCreate, AnimeResponse
router = APIRouter()

# ===========================================
#               jikan endpoints
# ===========================================

@router.get('jikan/top', summary='Jikan: Топ Аниме')
async def top_anime(client: JikanDepends):
    return await client.get_top_anime(limit=5)

@router.get('/jikan/search', summary='Jikan: Поиск')
async def search_anime(query: str, client: JikanDepends):
    return await client.search_anime(query=query)

@router.get('/jikan/{mal_id}', summary='Jikan: детали по mal id')
async def get_anime_full(mal_id: int, client: JikanDepends):
    return await client.get_anime_by_id(mal_id=mal_id)

# ===========================================
#               local database endpoints
# ===========================================

@router.get('/', response_model=list[AnimeResponse], summary='список всех аниме из дб')
async def get_all_anime(
    repo: AnimeRepoDepends,
    limit: int = Query(10, ge=1, le=100),
    min_score: float = Query(5.0, ge=0.0, le=10.0)
):
    return await repo.get_all(limit=limit, min_score=min_score)

@router.post('/', response_model=AnimeResponse, status_code=status.HTTP_201_CREATED)
async def create_anime(
    anime_in: AnimeCreate,
    repo: AnimeRepoDepends
):
    if await repo.exists_by_mal_id(anime_in.mal_id):
        return await repo.get_by_mal_id(anime_in.mal_id)
    
    return await repo.create(anime_in)

@router.get('/{anime_id}', response_model=AnimeResponse, summary='поиск по id базы данных')
async def get_anime_details(
    anime_id: int,
    repo: AnimeRepoDepends
):
    anime = await repo.get_by_mal_id(anime_id)
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'аниме не найдено в базе данных по внутреннему {anime_id}'
        )

    return anime

@router.get('/mal/{mal_id}', response_model=AnimeResponse, summary="Поиск в БД по MAL ID")
async def get_anime_by_mal_id(
    mal_id: int,
    repo: AnimeRepoDepends
):
    anime = await repo.get_by_mal_id(mal_id)
    
    if not anime:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'аниме не найдено в базе данных по mal_id {mal_id}'
        )
    return anime
