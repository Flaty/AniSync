from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.user_anime_list import WatchStatus


class AnimeShort(BaseModel):
    id: int
    mal_id: int
    title: str
    image_url: Optional[str] = None
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class UserAnimeListCreate(BaseModel):
    anime_id: int = Field(..., ge=1)
    status: WatchStatus
    score: Optional[float] = Field(None, ge=0.0, le=10.0)
    progress: Optional[int] = Field(None, ge=0)


class UserAnimeListUpdate(BaseModel):
    status: Optional[WatchStatus] = None
    score: Optional[float] = Field(None, ge=0.0, le=10.0)
    progress: Optional[int] = Field(None, ge=0)


class UserAnimeListResponse(BaseModel):
    id: int
    anime_id: int
    status: WatchStatus
    score: Optional[float] = None
    progress: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    anime: AnimeShort

    model_config = ConfigDict(from_attributes=True)
