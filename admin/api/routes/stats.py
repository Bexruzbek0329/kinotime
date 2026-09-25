"""Statistics routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models.admin import Admin
from database.models.movie import Movie
from database.repositories.user_repo import UserRepository
from database.repositories.movie_repo import MovieRepository
from database.repositories.search_repo import SearchRepository
from admin.api.middlewares.auth import get_current_admin

router = APIRouter()


@router.get("/dashboard")
async def dashboard_stats(
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    user_repo = UserRepository(session)
    movie_repo = MovieRepository(session)
    search_repo = SearchRepository(session)

    total_users = await user_repo.get_total_count()
    new_users_today = await user_repo.get_today_count()
    total_views = await movie_repo.get_total_views()
    searches_today = await search_repo.get_today_count()
    top_movies = await movie_repo.get_top_viewed(limit=10)
    not_found = await search_repo.get_not_found_searches(limit=20)
    popular_searches = await search_repo.get_popular_searches(limit=10)

    total_movies_result = await session.execute(select(func.count(Movie.id)))
    total_movies = total_movies_result.scalar_one()

    return {
        "total_users": total_users,
        "new_users_today": new_users_today,
        "total_movies": total_movies,
        "total_views": total_views,
        "searches_today": searches_today,
        "top_movies": [
            {"id": m.id, "title": m.title, "views_count": m.views_count}
            for m in top_movies
        ],
        "not_found_searches": not_found,
        "popular_searches": popular_searches,
    }
