from datetime import datetime
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

DEFAULT_SETTINGS = {
    "welcome_message": (
        "🎬 *KINO BOT*\n\nAssalomu alaykum! 👋\n\n"
        "Bu yerda sevimli filmlaringizni\ntez va qulay topishingiz mumkin.\n\n"
        "🔎 Kino nomi yoki kodini yuboring.\n\nYoki pastdagi menyudan foydalaning 👇"
    ),
    "not_found_message": "😔 *Kino topilmadi.*\n\n🔎 Boshqa nom bilan qidirib ko'ring.",
    "error_message": "😕 Nimadir xato ketdi.\n\nBirozdan keyin qayta urinib ko'ring.",
    "help_message": (
        "ℹ️ *YORDAM*\n\n"
        "🔎 *Qidirish* — kino yoki serial nomi yoki kodi orqali qidirish\n"
        "⭐ *Top kinolar* — mashhur reytingli filmlar\n"
        "👤 *Profil* — profilingiz va sevimlilar\n\n"
        "Kino/serial kodini bilsangiz, shunchaki kodni yuboring."
    ),
    "subscription_message": (
        "📢 *BOTDAN FOYDALANISH UCHUN*\n\nAvval kanalimizga obuna bo'ling 👇"
    ),
    "start_sticker_file_id": "",
    "not_found_sticker_file_id": "",
    "error_sticker_file_id": "",
    "movie_sticker_file_id": "",
    "stickers_enabled": "true",
    "admin_contact": "",
    "bot_description": (
        "🎬 Kinolar Olami Botiga xush kelibsiz!\n\n"
        "Bu yerda eng so'nggi premyeralar, mashhur filmlar va seriallarni tomosha qilishingiz mumkin.\n\n"
        "Boshlash uchun START tugmasini bosing! 👇"
    ),
    "bot_short_description": "Eng sara kino va seriallar olami 🎬",
    "sponsor_ad_enabled": "false",
    "sponsor_ad_text": "",
    "sponsor_ad_button_text": "",
    "sponsor_ad_button_url": "",
}


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
