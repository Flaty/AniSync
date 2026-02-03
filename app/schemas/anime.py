from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.models.anime import AnimeStatus, AnimeSeason

class AnimeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description='название аниме')
    title_english: Optional[str] = Field(None, min_length=1, max_length=255, description='название аниме на англ')
    synopsis : Optional[str] = Field(None, description='описание из аниме')
    score: Optional[float] = Field(None, ge=0.0, le=10.0, description='оценка аниме')
    episodes: Optional[int] = Field(None, ge=0, description='количество серий аниме')
    status: Optional[AnimeStatus] = Field(None, description='Статус (airing, finished, upcoming)')
    season: Optional[AnimeSeason] = Field(None, description='Сезон (winter, summer, fall etc..)')
    year: Optional[int] = Field(None, ge=1900, le=2100, description='Год выхода')
    image_url: Optional[str] = Field(None, description='url постера')

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True
    )


class AnimeCreate(AnimeBase):
    mal_id: int = Field(..., ge=1, description='mal id из jikan')

class AnimeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    title_english: Optional[str] = Field(None, max_length=255)
    synopsis: Optional[str] = Field(None)
    score: Optional[float] = Field(None, ge=0.0, le=10.0)
    episodes: Optional[int] = Field(None, ge=0)
    status: Optional[AnimeStatus] = Field(None)
    season: Optional[AnimeSeason] = Field(None)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    image_url: Optional[str] = Field(None)

    model_config = ConfigDict(
        from_attributes=True,
    )

class AnimeResponse(AnimeBase):
    id: int = Field(..., description="внутренний ид в дб")
    mal_id: int
    created_at: datetime = Field(..., description="дата создания")
    updated_at: Optional[datetime] = Field(None, description="дата обновления")