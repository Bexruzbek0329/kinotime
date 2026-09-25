"""Handle the 'check:subscription' callback after user clicks the verify button."""
import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import subscription_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.subscription_service import check_user_subscriptions
from bot.utils.deep_link import parse_start_param
from database.repositories.channel_repo import ChannelRepository
from database.repositories.setting_repo import SettingRepository
from config import settings

router = Router(name="subscription")
log = structlog.get_logger()


@router.callback_query(F.data == "check:subscription")
async def cb_check_subscription(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot,
) -> None:
    """
    Re-verify channel membership when the user taps "✅ Obunani tekshirish".

    - Still unsubscribed: refresh the keyboard with the remaining channels and
      show an alert.
    - Fully subscribed: show a success alert and display the main menu.
    """
    user_id = callback.from_user.id
    channel_repo = ChannelRepository(session)
    channels = await channel_repo.get_all_active()

    unsubscribed, admin_errors = await check_user_subscriptions(bot, user_id, channels)

    if unsubscribed:
        if user_id in settings.admin_id_list and admin_errors:
            alert_text = (
                "⚠️ DIQQAT ADMIN: Bot kanalda Admin emas!\n\n"
                "Telegramdan kanalingizga kiring va botni Administrator qilib qo'shing."
            )
            await callback.answer(alert_text, show_alert=True)
        else:
            await callback.answer("❌ Hali obuna bo‘lmadingiz!", show_alert=True)

        setting_repo = SettingRepository(session)
        msg = (
            await setting_repo.get("subscription_message")
            or "📢 *BOTDAN FOYDALANISH UCHUN*\n\nAvval quyidagi kanalimizga obuna bo‘ling 👇"
        )
        if user_id in settings.admin_id_list and admin_errors:
            msg += "\n\n⚠️ *ADMIN UCHUN:* Bot kanalda Admin emas! Telegramdan kanalga kirib, botni Administrator qilib qo'shing."

        kb = subscription_keyboard(unsubscribed, settings.bot_username)
        try:
            await callback.message.edit_text(msg, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            try:
                await callback.message.edit_reply_markup(reply_markup=kb)
            except Exception:
                pass
        log.info("subscription_still_missing", user_id=user_id, count=len(unsubscribed))
    else:
        await callback.answer(
            "✅ Rahmat! Endi botdan foydalanishingiz mumkin.",
            show_alert=True,
        )
        try:
            await callback.message.delete()
        except Exception:
            pass

        log.info("subscription_verified", user_id=user_id)

        # Check if user had a pending deep link (e.g. /start movie_42)
        state_data = await state.get_data()
        pending_link = state_data.get("pending_deep_link")
        await state.clear()

        setting_repo = SettingRepository(session)
        welcome = (
            await setting_repo.get("welcome_message") or "🎬 *Xush kelibsiz!*"
        )
        await callback.message.answer(
            welcome,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )

        if pending_link:
            deep = parse_start_param(pending_link)
            if deep and deep.get("type") == "movie":
                from bot.handlers.movie import send_movie_card
                await send_movie_card(callback.message, session, bot, deep["id"])
