import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class MovieStatus(str, enum.Enum):
    published = "published"
    hidden = "hidden"
    draft = "draft"


class ContentType(str, enum.Enum):
    movie = "movie"
    serial = "serial"


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        Index("ix_movies_code", "code"),
        Index("ix_movies_status", "status"),
        Index("ix_movies_title", "title"),
        Index("ix_movies_content_type", "content_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType), default=ContentType.movie, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    poster_file_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_seasons: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_episodes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    imdb_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    status: Mapped[MovieStatus] = mapped_column(
        Enum(MovieStatus), default=MovieStatus.draft, nullable=False
    )
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    videos = relationship(
        "MovieVideo", back_populates="movie", lazy="select", cascade="all, delete-orphan"
    )
    episodes = relationship(
        "Episode",
        back_populates="movie",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="Episode.season_number, Episode.episode_number",
    )
    genres = relationship(
        "Genre", secondary="movie_genres", back_populates="movies", lazy="select"
    )
    favorites = relationship("Favorite", back_populates="movie", lazy="select")
    ratings = relationship("Rating", back_populates="movie", lazy="select")
    views = relationship("View", back_populates="movie", lazy="select")
