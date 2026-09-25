from pydantic import BaseModel
from typing import List


class DashboardStats(BaseModel):
    total_users: int
    new_users_today: int
    total_movies: int
    total_views: int
    searches_today: int
    top_movies: List[dict]
    not_found_searches: List[dict]
