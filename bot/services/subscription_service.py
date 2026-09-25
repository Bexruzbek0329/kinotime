"""Check user membership in mandatory Telegram channels."""
from typing import List, Tuple
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
import structlog

log = structlog.get_logger()


async def check_user_subscriptions(
    bot: Bot,
    user_id: int,
    channels: list,
) -> Tuple[List[dict], List[str]]:
    """
    Verify that *user_id* is a full member of every channel in *channels*.

    Args:
        bot:      The :class:`~aiogram.Bot` instance.
        user_id:  Telegram user ID to check.
        channels: Iterable of ORM channel objects with ``channel_id``,
                  ``title``, and ``username`` attributes.

    Returns:
        (unsubscribed_list, admin_errors_list)
        - unsubscribed_list: list of dicts with {"title", "username"}
        - admin_errors_list: list of error descriptions (e.g. bot not admin)
    """
    unsubscribed: List[dict] = []
    admin_errors: List[str] = []

    for ch in channels:
        clean_u = str(ch.username).removeprefix("https://t.me/").removeprefix("http://t.me/").removeprefix("t.me/").lstrip("@")
        member = None

        # 1. Try numeric channel_id first
        try:
            member = await bot.get_chat_member(ch.channel_id, user_id)
        except (TelegramForbiddenError, TelegramBadRequest) as e1:
            # 2. Try @username as fallback if available
            if clean_u:
                try:
                    member = await bot.get_chat_member(f"@{clean_u}", user_id)
                except Exception as e2:
                    err_msg = str(e2) or str(e1)
                    log.warning(
                        "subscription_check_failed_both",
                        channel_id=ch.channel_id,
                        username=clean_u,
                        error=err_msg,
                        user_id=user_id,
                    )
                    admin_errors.append(f"@{clean_u}: {err_msg}")
                    unsubscribed.append({"title": ch.title, "username": ch.username})
                    continue
            else:
                err_msg = str(e1)
                log.warning(
                    "subscription_check_failed_id",
                    channel_id=ch.channel_id,
                    error=err_msg,
                    user_id=user_id,
                )
                admin_errors.append(f"ID {ch.channel_id}: {err_msg}")
                unsubscribed.append({"title": ch.title, "username": ch.username})
                continue
        except Exception as exc:
            log.error("subscription_unexpected_error", error=str(exc))
            unsubscribed.append({"title": ch.title, "username": ch.username})
            continue

        if member and member.status in ("left", "kicked"):
            unsubscribed.append({"title": ch.title, "username": ch.username})

    return unsubscribed, admin_errors
