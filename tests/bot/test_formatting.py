import pytest
from bot.utils.formatting import format_duration, format_number, format_movie_card, format_not_found, format_profile


def test_format_duration():
    assert format_duration(169) == "2 soat 49 daqiqa"
    assert format_duration(120) == "2 soat"
    assert format_duration(45) == "45 daqiqa"
    assert format_duration(None) == "N/A"
    assert format_duration(0) == "N/A"


def test_format_number():
    assert format_number(1000) == "1 000"
    assert format_number(1234567) == "1 234 567"
    assert format_number(0) == "0"


def test_format_movie_card():
    movie = {
        "title": "Interstellar",
        "original_title": "Interstellar",
        "imdb_rating": 8.7,
        "year": 2014,
        "country": "USA",
        "duration_minutes": 169,
        "description": "Insoniyat kelajagini saqlab qolish uchun kosmik missiyaga yo'l olgan astronavtlar.",
        "views_count": 10540,
    }
    genres = ["Fantastika", "Drama"]
    caption = format_movie_card(movie, genres, avg_rating=4.8)

    assert "Interstellar" in caption
    assert "8.7" in caption
    assert "2014" in caption
    assert "Fantastika • Drama" in caption
    assert "10 540" in caption


def test_format_not_found():
    res = format_not_found("Avatar 5")
    assert "Avatar 5" in res
    assert "Kino topilmadi" in res


def test_format_profile():
    res = format_profile({"telegram_id": 123456789, "joined_at": "2026-09-24"}, {"views": 15, "ratings": 5})
    assert "123456789" in res
    assert "15" in res
    assert "5" in res


def test_format_serial_card():
    serial = {
        "title": "Qashqirlar makoni",
        "original_title": "Kurtlar Vadisi",
        "imdb_rating": 8.1,
        "year": 2003,
        "country": "Turkiya",
        "content_type": "serial",
        "total_seasons": 4,
        "total_episodes": 97,
        "description": "Turkiyaning eng mashhur kriminal seriali.",
        "views_count": 5200,
    }
    genres = ["Jangari", "Kriminal"]
    caption = format_movie_card(serial, genres, avg_rating=4.9)

    assert "Qashqirlar makoni" in caption
    assert "Serial haqida:" in caption
    assert "4 mavsum" in caption
    assert "97 qism" in caption

