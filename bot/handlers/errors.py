"""Global unhandled-exception catcher."""
import traceback

import structlog
from aiogram import Router
from aiogram.types import ErrorEvent

from bot.keyboards.inline import back_to_menu_keyboard

router = Router(name="errors")
log = structlog.get_logger()


@router.errors()
async def global_error_handler(event: ErrorEvent) -> None:
    """
    Catch any exception that propagates out of a handler or middleware.

    - Logs the full traceback via structlog.
    - Sends a user-friendly error message if the originating update was
      a :class:`~aiogram.types.Message` or :class:`~aiogram.types.CallbackQuery`.
    - Silently swallows secondary errors so the bot keeps running.
    """
    log.error(
        "unhandled_exception",
        error=str(event.exception),
        traceback=traceback.format_exc(),
    )

    error_text = (
        "\U0001f615 Nimadir xato ketdi.\n\n"
        "Birozdan keyin qayta urinib ko\u2018ring."
    )

    update = event.update

    if update.message:
        try:
            await update.message.answer(
                error_text,
                reply_markup=back_to_menu_keyboard(),
            )
        except Exception as exc:
            log.warning("error_handler_reply_failed", error=str(exc))

    elif update.callback_query:
        try:
            await update.callback_query.answer(
                "\U0001f615 Xato yuz berdi.",
                show_alert=True,
            )
        except Exception as exc:
            log.warning("error_handler_cb_answer_failed", error=str(exc))
