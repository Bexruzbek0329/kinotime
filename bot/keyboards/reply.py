"""Reply keyboard definitions."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Return the main persistent reply keyboard shown to every user."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="\U0001f50e Qidirish"), KeyboardButton(text="\u2b50 Top kinolar")],
            [KeyboardButton(text="\U0001f464 Profil"), KeyboardButton(text="\u2139\ufe0f Yordam")],
        ],
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Kino yoki serial kodini yozing...",
    )
