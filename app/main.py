from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.config import settings
from app.external.jikan_client import JikanClient
from app.tasks.broker import broker
import app.tasks.anime_tasks  # noqa: F401
from app.api import anime, auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.startup()

    jikan_client = JikanClient()
    app.state.jikan_client = jikan_client

    redis_client = aioredis.from_url(settings.redis_url)
    app.state.redis = redis_client

    yield

    await jikan_client.close()
    await redis_client.aclose()
    await broker.shutdown()


app = FastAPI(
    title='AniSync Api',
    version='0.1 beta',
    lifespan=lifespan
)

app.include_router(anime.router, prefix='/anime', tags=['Anime'])
app.include_router(auth.router, prefix='/auth', tags=['Auth'])
app.include_router(users.router, prefix='/users', tags=['Users'])


@app.get('/health')
async def status():
    return {'status': 'AniSync онлайн!'}
