from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager

from app.external.jikan_client import JikanClient
from app.api import anime

@asynccontextmanager
async def lifespan(app: FastAPI):
    jikan_client = JikanClient()
    app.state.jikan_client = jikan_client
    yield
    await jikan_client.close()

app = FastAPI(
    title='AniSync Api',
    version='0.1 beta',
    lifespan=lifespan
)

app.include_router(anime.router, prefix='/anime', tags=['Anime'])

@app.get('/health')
async def status():
    return {'status': 'AniSync онлайн!'}