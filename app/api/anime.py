from fastapi import APIRouter
from app.dependencies import AnimeRepoDepends, JikanDepends
router = APIRouter(
    prefix='/anime',
    tags=['Anime']
)

@router.get('/top/anime')
async def top_anime(client: JikanDepends):
    top = await client.get_top_anime(limit=5)
    return top

@router.get('/anime/{mal_id}')
async def get_anime_full(mal_id: int, client: JikanDepends):
    anime_full = await client.get_anime_by_id(mal_id=mal_id)
    return anime_full

@router.get('/search/anime/')
async def search_anime(query: str, client: JikanDepends):
    search = await client.search_anime(query=query)
    return search


@router.post('/anime/test')
async def test_create_anime(repo: AnimeRepoDepends):
    test_anime = {
        'mal_id': 1337,
        'title': 'Я переродился в другом мире банкоматом Т-Банка',
        'title_english': 'I was reborn in another world as a ATM t-bank',
        'synopsis': 't-bank',
        'score': 10.0,
        'episodes': 24,
        'status': 'finished',
        'season': 'winter',
        'year': 2026,
        'image_url': 'https://avatars.mds.yandex.net/get-altay/10812438/2a0000018aebbf3ecb7cf265b0dfdc18840e/XXL_height'
    }

    exists = await repo.exists_by_mal_id(1337)
    if exists:
        anime = await repo.get_by_mal_id(1337)
        return {
            'message': 'anime in database',
            'anime_id': anime.id,
            'title': anime.title,
            'created_at': anime.created_at   
        }
    
    created = await repo.create(test_anime)
    
    return {
        'message': 'Anime created successfully desu~! ✨',
        'anime_id': created.id,
        'title': created.title,
        'score': created.score,
        'created_at': created.created_at
    }

@router.get('/anime/db/all')
async def get_all_anime(
    repo: AnimeRepoDepends,
    limit: int = 10,
    min_score: float = 5.0
):
    anime_list = await repo.get_all(limit=limit, min_score=min_score)

    return {
        'count': len(anime_list),
        'anime': [
            {
                'id': a.id,
                'mal_id': a.mal_id,
                'title': a.title,
                'score': a.score,
                'episodes': a.episodes
            }
            for a in anime_list
        ]
    }