import httpx
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.models.anime import AnimeSeason, AnimeStatus


class JikanClient:
    def __init__(self):
        self.base_url = 'https://api.jikan.moe/v4'
        self.client = httpx.AsyncClient(timeout=10.0)
        self.rate_limiter = AsyncLimiter(3, 1)

    @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(httpx.HTTPStatusError)
    )
    async def _request(self, method: str, endpoint: str, **kwargs):
        async with self.rate_limiter:
            url = f'{self.base_url}/{endpoint}'
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
    
    async def get_top_anime(self, limit: int = 10):
        data = await self._request('GET', 'top/anime', params={'limit': limit})
        return data['data']
    

    async def get_anime_by_id(self, mal_id: int):
        data = await self._request('GET', f'anime/{mal_id}/full')
        return data['data']

    async def search_anime(
            self, 
            query: str,
            page: int = 1, 
            limit: int = 25,
            type: str | None = None,
            status: AnimeStatus | None = None,
            season: AnimeSeason | None = None,
            order_by: str | None = 'scored_by'):
        params = {'q': query, 'page': page, 'limit': limit, 'type': type, 'status': status, 'order_by' : order_by, 'season': season}
        data = await self._request('GET', 'anime/', params=params)
        return data['data']
    async def close(self):
        await self.client.aclose()
