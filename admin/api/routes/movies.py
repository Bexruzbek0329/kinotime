"""Movie CRUD routes."""
import math
import random
import string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, Integer
from sqlalchemy.orm import selectinload
from database.engine import get_db
from database.models.movie import Movie, MovieStatus
from database.models.movie_video import MovieVideo, VideoQuality
from database.models.episode import Episode
from database.models.genre import Genre, MovieGenre
from database.models.audit_log import AuditLog
from database.models.admin import Admin
from database.repositories.movie_repo import MovieRepository
from admin.schemas.movie import (
    MovieCreate,
    MovieUpdate,
    MovieOut,
    PaginatedMovies,
    EpisodeCreate,
    EpisodeBatchCreate,
    EpisodeOut,
)
from admin.api.middlewares.auth import get_current_admin
from typing import List, Optional

router = APIRouter()


async def generate_next_code(session: AsyncSession) -> str:
    """
    Generate a short, human-friendly code for a new content item.

    Logic:
      - Find the highest numeric code currently in the DB.
      - Add a small random gap (1-3) to it.
      - Start from 1 if no items exist yet.
      - Keeps codes short (1-digit to N-digit as library grows).
    """
    import random
    from sqlalchemy import func as sqlfunc

    result = await session.execute(
        select(sqlfunc.max(sqlfunc.cast(Movie.code, Integer))).where(
            Movie.code.regexp_match(r"^\d+$")
        )
    )
    max_code = result.scalar_one_or_none()
    if max_code is None:
        next_code = 1
    else:
        next_code = int(max_code) + random.randint(1, 3)

    # Ensure uniqueness (rare gap collision check)
    for _ in range(20):
        code_str = str(next_code)
        existing = await session.execute(select(Movie).where(Movie.code == code_str))
        if not existing.scalar_one_or_none():
            return code_str
        next_code += 1

    # Absolute fallback (should never reach here)
    return str(next_code)


async def get_or_create_genre(name: str, session: AsyncSession) -> Genre:
    result = await session.execute(select(Genre).where(Genre.name == name))
    genre = result.scalar_one_or_none()
    if not genre:
        genre = Genre(name=name)
        session.add(genre)
        await session.flush()
    return genre


def movie_to_out(movie: Movie) -> MovieOut:
    return MovieOut(
        id=movie.id,
        code=movie.code,
        content_type=movie.content_type.value if movie.content_type else "movie",
        title=movie.title,
        original_title=movie.original_title,
        poster_file_id=movie.poster_file_id,
        description=movie.description,
        year=movie.year,
        country=movie.country,
        duration_minutes=movie.duration_minutes,
        total_seasons=movie.total_seasons,
        total_episodes=movie.total_episodes,
        imdb_rating=float(movie.imdb_rating) if movie.imdb_rating else None,
        status=movie.status.value,
        views_count=movie.views_count,
        created_at=movie.created_at,
        updated_at=movie.updated_at,
        genres=[g.name for g in (movie.genres or [])],
        videos=[
            {
                "id": v.id,
                "quality": v.quality.value,
                "telegram_file_id": v.telegram_file_id,
                "duration_seconds": v.duration_seconds,
                "file_size_bytes": v.file_size_bytes,
            }
            for v in (movie.videos or [])
        ],
        episodes=[
            {
                "id": ep.id,
                "movie_id": ep.movie_id,
                "season_number": ep.season_number,
                "episode_number": ep.episode_number,
                "title": ep.title,
                "telegram_file_id": ep.telegram_file_id,
                "quality": ep.quality,
                "duration_seconds": ep.duration_seconds,
                "file_size_bytes": ep.file_size_bytes,
                "views_count": ep.views_count,
                "created_at": ep.created_at,
            }
            for ep in (movie.episodes or [])
        ],
    )


@router.get("", response_model=PaginatedMovies)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    content_type: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = MovieRepository(session)
    movies, total = await repo.get_paginated_admin(
        page=page, per_page=per_page, search=search, status=status, content_type=content_type
    )
    ids = [m.id for m in movies]
    result = await session.execute(
        select(Movie)
        .where(Movie.id.in_(ids))
        .options(
            selectinload(Movie.videos),
            selectinload(Movie.episodes),
            selectinload(Movie.genres),
        )
        .order_by(Movie.created_at.desc())
    )
    movies = result.scalars().all()
    return PaginatedMovies(
        items=[movie_to_out(m) for m in movies],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=max(1, math.ceil(total / per_page)),
    )


@router.post("", response_model=MovieOut)
async def create_movie(
    body: MovieCreate,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    # Generate unique sequential code
    code = await generate_next_code(session)

    from database.models.movie import ContentType
    movie = Movie(
        code=code,
        content_type=ContentType(body.content_type) if body.content_type else ContentType.movie,
        title=body.title,
        original_title=body.original_title,
        poster_file_id=body.poster_file_id,
        description=body.description,
        year=body.year,
        country=body.country,
        duration_minutes=body.duration_minutes,
        total_seasons=body.total_seasons,
        total_episodes=body.total_episodes,
        imdb_rating=body.imdb_rating,
        status=MovieStatus(body.status),
    )
    session.add(movie)
    await session.flush()

    # Genres
    for genre_name in body.genres:
        genre = await get_or_create_genre(genre_name.strip(), session)
        mg = MovieGenre(movie_id=movie.id, genre_id=genre.id)
        session.add(mg)

    # Videos
    for v in body.videos:
        video = MovieVideo(
            movie_id=movie.id,
            quality=VideoQuality(v.quality),
            telegram_file_id=v.telegram_file_id,
            duration_seconds=v.duration_seconds,
            file_size_bytes=v.file_size_bytes,
        )
        session.add(video)

    # Audit log
    log_entry = AuditLog(
        admin_id=admin.id,
        action="create_movie",
        entity_type="movie",
        entity_id=movie.id,
        new_value={"title": movie.title},
    )
    session.add(log_entry)
    await session.commit()

    result = await session.execute(
        select(Movie)
        .where(Movie.id == movie.id)
        .options(
            selectinload(Movie.videos),
            selectinload(Movie.episodes),
            selectinload(Movie.genres),
        )
    )
    movie = result.scalar_one()
    return movie_to_out(movie)


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    result = await session.execute(
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.videos),
            selectinload(Movie.episodes),
            selectinload(Movie.genres),
        )
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie_to_out(movie)


@router.put("/{movie_id}", response_model=MovieOut)
async def update_movie(
    movie_id: int,
    body: MovieUpdate,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    result = await session.execute(
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.videos),
            selectinload(Movie.episodes),
            selectinload(Movie.genres),
        )
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    old_val = {"title": movie.title, "status": movie.status.value}
    update_data = body.model_dump(exclude_none=True, exclude={"genres"})
    if "status" in update_data:
        update_data["status"] = MovieStatus(update_data["status"])
    for k, v in update_data.items():
        setattr(movie, k, v)

    if body.genres is not None:
        await session.execute(
            delete(MovieGenre).where(MovieGenre.movie_id == movie_id)
        )
        for genre_name in body.genres:
            genre = await get_or_create_genre(genre_name.strip(), session)
            mg = MovieGenre(movie_id=movie.id, genre_id=genre.id)
            session.add(mg)

    log_entry = AuditLog(
        admin_id=admin.id,
        action="update_movie",
        entity_type="movie",
        entity_id=movie_id,
        old_value=old_val,
    )
    session.add(log_entry)
    await session.commit()

    result = await session.execute(
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.videos),
            selectinload(Movie.episodes),
            selectinload(Movie.genres),
        )
    )
    movie = result.scalar_one()
    return movie_to_out(movie)


@router.delete("/{movie_id}")
async def delete_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    movie = await session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    log_entry = AuditLog(
        admin_id=admin.id,
        action="delete_movie",
        entity_type="movie",
        entity_id=movie_id,
        old_value={"title": movie.title},
    )
    session.add(log_entry)
    await session.delete(movie)
    await session.commit()
    return {"ok": True}


@router.post("/{movie_id}/videos")
async def add_video(
    movie_id: int,
    body: dict,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    movie = await session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    video = MovieVideo(
        movie_id=movie_id,
        quality=VideoQuality(body["quality"]),
        telegram_file_id=body["telegram_file_id"],
        duration_seconds=body.get("duration_seconds", 0),
        file_size_bytes=body.get("file_size_bytes", 0),
    )
    session.add(video)
    await session.commit()
    return {"id": video.id, "quality": video.quality.value}


@router.delete("/{movie_id}/videos/{video_id}")
async def delete_video(
    movie_id: int,
    video_id: int,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    result = await session.execute(
        select(MovieVideo).where(
            MovieVideo.id == video_id, MovieVideo.movie_id == movie_id
        )
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    await session.delete(video)
    await session.commit()
    return {"ok": True}


# ----------------------------------------------------------------------
# Serial Episodes Management
# ----------------------------------------------------------------------


@router.get("/{movie_id}/episodes", response_model=List[EpisodeOut])
async def list_movie_episodes(
    movie_id: int,
    season: Optional[int] = None,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Retrieve all episodes for a serial, optionally filtered by season."""
    repo = MovieRepository(session)
    episodes = await repo.get_episodes(movie_id, season_number=season)
    return [
        EpisodeOut(
            id=ep.id,
            movie_id=ep.movie_id,
            season_number=ep.season_number,
            episode_number=ep.episode_number,
            title=ep.title,
            telegram_file_id=ep.telegram_file_id,
            quality=ep.quality,
            duration_seconds=ep.duration_seconds,
            file_size_bytes=ep.file_size_bytes,
            views_count=ep.views_count,
            created_at=ep.created_at,
        )
        for ep in episodes
    ]


@router.post("/{movie_id}/episodes", response_model=EpisodeOut)
async def add_movie_episode(
    movie_id: int,
    body: EpisodeCreate,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Add or update an episode for a serial."""
    movie = await session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    repo = MovieRepository(session)
    ep = await repo.add_or_update_episode(
        movie_id=movie_id,
        season_number=body.season_number,
        episode_number=body.episode_number,
        telegram_file_id=body.telegram_file_id.strip(),
        quality=body.quality,
        title=body.title,
        duration_seconds=body.duration_seconds,
        file_size_bytes=body.file_size_bytes,
    )
    await session.commit()
    return EpisodeOut(
        id=ep.id,
        movie_id=ep.movie_id,
        season_number=ep.season_number,
        episode_number=ep.episode_number,
        title=ep.title,
        telegram_file_id=ep.telegram_file_id,
        quality=ep.quality,
        duration_seconds=ep.duration_seconds,
        file_size_bytes=ep.file_size_bytes,
        views_count=ep.views_count,
        created_at=ep.created_at,
    )


@router.post("/{movie_id}/episodes/batch", response_model=List[EpisodeOut])
async def add_movie_episodes_batch(
    movie_id: int,
    body: EpisodeBatchCreate,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Batch add multiple sequential episodes from a list of Telegram file_ids."""
    movie = await session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    repo = MovieRepository(session)
    added = []
    curr_ep = body.start_episode_number
    for fid in body.file_ids:
        clean_fid = fid.strip()
        if not clean_fid:
            continue
        ep = await repo.add_or_update_episode(
            movie_id=movie_id,
            season_number=body.season_number,
            episode_number=curr_ep,
            telegram_file_id=clean_fid,
            quality=body.quality,
            title=f"{curr_ep}-qism",
        )
        added.append(
            EpisodeOut(
                id=ep.id,
                movie_id=ep.movie_id,
                season_number=ep.season_number,
                episode_number=ep.episode_number,
                title=ep.title,
                telegram_file_id=ep.telegram_file_id,
                quality=ep.quality,
                duration_seconds=ep.duration_seconds,
                file_size_bytes=ep.file_size_bytes,
                views_count=ep.views_count,
                created_at=ep.created_at,
            )
        )
        curr_ep += 1
    await session.commit()
    return added


@router.delete("/{movie_id}/episodes/{episode_id}")
async def delete_movie_episode(
    movie_id: int,
    episode_id: int,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Delete an episode from a serial."""
    repo = MovieRepository(session)
    deleted = await repo.delete_episode(movie_id, episode_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Episode not found")
    await session.commit()
    return {"ok": True}
