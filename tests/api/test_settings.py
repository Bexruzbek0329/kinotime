import pytest
from database.models.setting import DEFAULT_SETTINGS


def test_default_settings_keys():
    assert "bot_description" in DEFAULT_SETTINGS
    assert "bot_short_description" in DEFAULT_SETTINGS
    assert "welcome_message" in DEFAULT_SETTINGS
    assert "start_sticker_file_id" in DEFAULT_SETTINGS
    assert "stickers_enabled" in DEFAULT_SETTINGS


def test_bot_description_length():
    # Telegram limit for setMyDescription is 512 chars
    desc = DEFAULT_SETTINGS["bot_description"]
    assert len(desc) <= 512
    # Telegram limit for setMyShortDescription is 120 chars
    short_desc = DEFAULT_SETTINGS["bot_short_description"]
    assert len(short_desc) <= 120
