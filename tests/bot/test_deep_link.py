from bot.utils.deep_link import parse_start_param, make_movie_deep_link


def test_parse_start_param():
    assert parse_start_param("movie_12345") == {"type": "movie", "id": 12345}
    assert parse_start_param("movie_abc") is None
    assert parse_start_param(None) is None
    assert parse_start_param("") is None
    assert parse_start_param("other_param") is None


def test_make_movie_deep_link():
    link = make_movie_deep_link("SuperKinoBot", 555)
    assert link == "https://t.me/SuperKinoBot?start=movie_555"
