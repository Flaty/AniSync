from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

anime_genres = Table(
    'anime_genres',
    Base.metadata,
    Column('anime_id', Integer, ForeignKey('anime.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genre.id', ondelete='CASCADE'), primary_key=True)
)

class Genre(Base):
    __tablename__ = 'genre'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    
    animes: Mapped[list['Anime']] = relationship(
        'Anime', secondary=anime_genres, back_populates='genres'
    )