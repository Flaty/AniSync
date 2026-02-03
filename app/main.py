from fastapi import FastAPI, Request, Depends
from typing import Annotated
from contextlib import asynccontextmanager
from external.jikan_client import JikanClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    jikan_client = JikanClient()
    app.state.jikan_client = jikan_client

    yield

    await jikan_client.close()

app = FastAPI(lifespan=lifespan)
    
def get_jikan_client(request: Request):
    client = request.app.state.jikan_client
    if client is None:
        raise RuntimeError('Jikan не инцилизрован')
    return client

JikanDepends = Annotated[JikanClient, Depends(get_jikan_client)]

@app.get('/health')
async def status():
    return {'status': 'AniSync онлайн!'}

@app.get('/top/anime')
async def top_anime(client: JikanDepends):
    top = await client.get_top_anime(limit=5)
    return top

@app.get('/anime/{mal_id}')
async def get_anime_full(mal_id: int, client: JikanDepends):
    anime_full = await client.get_anime_by_id(mal_id=mal_id)
    return anime_full

@app.get('/search/anime/')
async def search_anime(query: str, client: JikanDepends):
    search = await client.search_anime(query=query)
    return search