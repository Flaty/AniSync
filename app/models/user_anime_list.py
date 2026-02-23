from __future__ import annotations
import enum
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from app.models.base import Base
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.anime import Anime


class WatchStatus(enum.Enum):
    WATCHING = 'watching'
    COMPLETED = 'completed'
    PLAN_TO_WATCH = 'plan_to_watch'
    DROPPED = 'dropped'
    ON_HOLD = 'on_hold'


class UserAnimeList(Base):
    __tablename__ = 'user_anime_list'

    __table_args__ = (
        UniqueConstraint('user_id', 'anime_id', name='uq_user_anime'),
        CheckConstraint('score >= 0 AND score <= 10', name='ck_score_range'),
        CheckConstraint('progress >= 0', name='ck_progress_non_negative'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    anime_id: Mapped[int] = mapped_column(
        ForeignKey('anime.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    status: Mapped[WatchStatus] = mapped_column(nullable=False)
    score: Mapped[float | None] = mapped_column(nullable=True)
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="anime_list")
    anime: Mapped["Anime"] = relationship("Anime", lazy="selectin")
