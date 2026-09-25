import pytest
from pydantic import ValidationError
from admin.schemas.movie import MovieCreate, VideoCreate
from admin.schemas.channel import ChannelCreate
from admin.schemas.auth import LoginRequest


def test_movie_create_schema():
    m = MovieCreate(
        title="Inception",
        year=2010,
        imdb_rating=8.8,
        status="published",
        genres=["Action", "Sci-Fi"],
        videos=[
            VideoCreate(quality="720p", telegram_file_id="BAACAgIAAxk...")
        ]
    )
    assert m.title == "Inception"
    assert m.imdb_rating == 8.8
    assert len(m.videos) == 1
    assert m.videos[0].quality == "720p"


def test_movie_create_invalid_rating():
    with pytest.raises(ValidationError):
        MovieCreate(title="Test", imdb_rating=11.0)


def test_channel_create_schema():
    ch = ChannelCreate(
        channel_id=-100192837465,
        username="kinolar_olami",
        title="Kinolar Olami Rasmiy"
    )
    assert ch.channel_id == -100192837465
    assert ch.is_active is True


def test_login_request():
    req = LoginRequest(username="admin", password="password123")
    assert req.username == "admin"


def test_episode_schemas():
    from admin.schemas.movie import EpisodeCreate, EpisodeBatchCreate

    single = EpisodeCreate(
        season_number=1,
        episode_number=5,
        title="5-qism",
        telegram_file_id="BAACAgIAAxk...",
        quality="1080p",
    )
    assert single.season_number == 1
    assert single.episode_number == 5
    assert single.quality == "1080p"

    batch = EpisodeBatchCreate(
        season_number=2,
        start_episode_number=1,
        quality="720p",
        file_ids=["file_1", "file_2", "file_3"],
    )
    assert batch.season_number == 2
    assert len(batch.file_ids) == 3

