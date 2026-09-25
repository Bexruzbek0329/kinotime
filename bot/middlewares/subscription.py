"""Mandatory channel subscription enforcement middleware."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.channel_repo import ChannelRepository
from database.repositories.setting_repo import SettingRepository
from bot.keyboards.inline import subscription_keyboard
from bot.services.subscription_service import check_user_subscriptions
from config import settings
import structlog

log = structlog.get_logger()


class SubscriptionMiddleware(BaseMiddleware):
    """
    Check that the user is a member of all active mandatory channels.

    If any channel is unsubscribed:
    - A subscription prompt with URL buttons is sent to the user.
    - The handler chain is terminated so no bot feature is accessible.

    Exemptions:
    - The ``check:subscription`` callback is passed through so the
      user can trigger the membership re-check.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession | None = data.get("session")
        bot: Bot | None = data.get("bot")

        if not session or not bot:
            return await handler(event, data)

        user_id: int | None = None

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            cb_data = event.data or ""
            if cb_data == "check:subscription":
                # Let the dedicated subscription callback handler process this
                return await handler(event, data)
            user_id = event.from_user.id if event.from_user else None
        else:
            return await handler(event, data)

        if not user_id:
            return await handler(event, data)

        channel_repo = ChannelRepository(session)
        channels = await channel_repo.get_all_active()
        if not channels:
            return await handler(event, data)

        unsubscribed, admin_errors = await check_user_subscriptions(bot, user_id, channels)

        if not unsubscribed:
            return await handler(event, data)

        # If user sent /start with a deep link, remember it for after subscription
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            parts = event.text.split(maxsplit=1)
            if len(parts) > 1:
                state: FSMContext | None = data.get("state")
                if state:
                    await state.update_data(pending_deep_link=parts[1])

        # User has not joined one or more channels — block and prompt
        setting_repo = SettingRepository(session)
        msg = (
            await setting_repo.get("subscription_message")
            or "📢 *BOTDAN FOYDALANISH UCHUN*\n\nAvval quyidagi kanalimizga obuna bo‘ling 👇"
        )

        kb = subscription_keyboard(unsubscribed, settings.bot_username)

        # If user is in admin list and bot has permission issues in the channel:
        if user_id in settings.admin_id_list and admin_errors:
            msg += "\n\n⚠️ *ADMIN UCHUN:* Bot kanalda Admin emas! Telegramdan kanalga kirib, botni Administrator qilib qo'shing."

        if isinstance(event, Message):
            await event.answer(msg, reply_markup=kb, parse_mode="Markdown")
        elif isinstance(event, CallbackQuery):
            await event.answer("Avval kanalga obuna bo‘ling!", show_alert=True)
            await event.message.answer(msg, reply_markup=kb, parse_mode="Markdown")

        return  # Short-circuit
