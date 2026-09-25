from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class VideoCreate(BaseModel):
    quality: str  # 360p, 480p, 720p, 1080p, 4K
    telegram_file_id: str
    duration_seconds: int = 0
    file_size_bytes: int = 0


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quality: str
    telegram_file_id: str
    duration_seconds: int
    file_size_bytes: int


class EpisodeCreate(BaseModel):
    season_number: int = 1
    episode_number: int
    title: Optional[str] = None
    telegram_file_id: str
    quality: str = "720p"
    duration_seconds: int = 0
    file_size_bytes: int = 0


class EpisodeBatchCreate(BaseModel):
    season_number: int = 1
    start_episode_number: int = 1
    quality: str = "720p"
    file_ids: List[str]  # sequential list of file_ids


class EpisodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    season_number: int
    episode_number: int
    title: Optional[str] = None
    telegram_file_id: str
    quality: str
    duration_seconds: int
    file_size_bytes: int
    views_count: int
    created_at: datetime


class MovieCreate(BaseModel):
    title: str
    content_type: str = "movie"   # "movie" | "serial"
    original_title: Optional[str] = None
    poster_file_id: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    country: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_seasons: Optional[int] = None
    total_episodes: Optional[int] = None
    imdb_rating: Optional[float] = Field(None, ge=0, le=10)
    status: str = "draft"
    genres: List[str] = []
    videos: List[VideoCreate] = []


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[str] = None
    original_title: Optional[str] = None
    poster_file_id: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    country: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_seasons: Optional[int] = None
    total_episodes: Optional[int] = None
    imdb_rating: Optional[float] = Field(None, ge=0, le=10)
    status: Optional[str] = None
    genres: Optional[List[str]] = None


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    content_type: str = "movie"
    title: str
    original_title: Optional[str]
    poster_file_id: Optional[str]
    description: Optional[str]
    year: Optional[int]
    country: Optional[str]
    duration_minutes: Optional[int]
    total_seasons: Optional[int] = None
    total_episodes: Optional[int] = None
    imdb_rating: Optional[float]
    status: str
    views_count: int
    created_at: datetime
    updated_at: datetime
    genres: List[str] = []
    videos: List[VideoOut] = []
    episodes: List[EpisodeOut] = []


class PaginatedMovies(BaseModel):
    items: List[MovieOut]
    total: int
    page: int
    per_page: int
    total_pages: int
