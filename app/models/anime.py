from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime
from datetime import datetime, timezone
import enum

class Base(DeclarativeBase):
    pass

class AnimeStatus(enum.Enum):
    AIRING = 'airing'
    FINISHED = 'finished'
    UPCOMING = 'upcoming'

class AnimeSeason(enum.Enum):
    WINTER = 'winter'
    SUMMER = 'summer'
    SPRING = 'spring'
    FALL = 'fall'

class Anime(Base):
    __tablename__ = 'anime'

    id: Mapped[int] = mapped_column(primary_key=True)
    mal_id: Mapped[int] = mapped_column(unique=True, nullable=True)
    title: Mapped[str] = mapped_column(nullable=False)
    title_english: Mapped[str] = mapped_column(nullable=True)
    title_japanese: Mapped[str] = mapped_column(nullable=True)
    synopsis: Mapped[str] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(nullable=True)
    episodes: Mapped[int] = mapped_column(nullable=True)
    status: Mapped[AnimeStatus] = mapped_column(nullable=True)
    season: Mapped[AnimeSeason] = mapped_column(nullable=True)
    year: Mapped[int] = mapped_column(nullable=True)
    image_url: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)) 
