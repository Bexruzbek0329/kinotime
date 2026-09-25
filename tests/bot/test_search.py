from bot.utils.search import normalize_query, fuzzy_search_score, is_movie_code


def test_normalize_query():
    assert normalize_query("  Avatar  2  ") == "avatar 2"
    assert normalize_query("INTERSTELLAR") == "interstellar"


def test_is_movie_code():
    assert is_movie_code("10245") is True
    assert is_movie_code("1") is True
    assert is_movie_code("avatar") is False
    assert is_movie_code("10245a") is False
    assert is_movie_code(" 123 ") is True


def test_fuzzy_search_score():
    assert fuzzy_search_score("avatar", "Avatar") == 100
    assert fuzzy_search_score("avatar", "Avatar: The Way of Water") >= 80
    assert fuzzy_search_score("interstellar", "Inception") == 0


def test_known_menu_texts():
    from bot.handlers.search import KNOWN_MENU_TEXTS
    assert "🔍 Qidirish" in KNOWN_MENU_TEXTS
    assert "⭐ Top kinolar" in KNOWN_MENU_TEXTS
    assert "👤 Profil" in KNOWN_MENU_TEXTS
    assert "ℹ️ Yordam" in KNOWN_MENU_TEXTS

