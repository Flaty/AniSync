from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager

from app.external.jikan_client import JikanClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    jikan_client = JikanClient()
    app.state.jikan_client = jikan_client
    yield
    await jikan_client.close()

app = FastAPI(lifespan=lifespan)

