from bot.keyboards.reply import main_menu_keyboard


def test_main_menu_keyboard_buttons():
    kb = main_menu_keyboard()
    button_texts = [btn.text for row in kb.keyboard for btn in row]
    
    # Verify Premyeralar is removed
    assert not any("Premyeralar" in text for text in button_texts)
    # Verify Kino is removed
    assert not any(text == "🎬 Kino" for text in button_texts)
    # Verify Serial is removed
    assert not any("Serial" in text for text in button_texts)

    # Verify expected 4 menu items exist in 2x2 layout
    assert "🔎 Qidirish" in button_texts
    assert "⭐ Top kinolar" in button_texts
    assert "👤 Profil" in button_texts
    assert "ℹ️ Yordam" in button_texts
    assert len(button_texts) == 4


def test_serial_card_keyboard():
    from bot.keyboards.inline import serial_card_keyboard

    episodes = [
        {"season_number": 1, "episode_number": 1},
        {"season_number": 1, "episode_number": 2},
        {"season_number": 2, "episode_number": 1},
    ]
    kb = serial_card_keyboard(
        movie_id=1,
        episodes=episodes,
        selected_season=1,
        is_favorite=False,
        user_rating=4,
        bot_username="test_bot",
    )
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    texts = [btn.text for btn in all_buttons]

    # Verify season buttons
    assert any("1-Fasl" in t for t in texts)
    assert any("2-Fasl" in t for t in texts)
    # Verify episode 1 and 2 buttons
    assert "1-qism" in texts
    assert "2-qism" in texts


def test_episode_video_keyboard():
    from bot.keyboards.inline import episode_video_keyboard

    kb = episode_video_keyboard(
        movie_id=1,
        season_number=1,
        current_episode=2,
        has_prev=True,
        has_next=True,
        is_favorite=False,
    )
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    texts = [btn.text for btn in all_buttons]

    assert any("Oldingi qism" in t or "1-qism" in t for t in texts)
    assert any("Keyingi qism" in t or "3-qism" in t for t in texts)
    assert "📋 Barcha qismlar" in texts
    assert "🏠 Bosh menyu" in texts

