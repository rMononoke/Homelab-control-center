import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger("bot.auth")


class AuthMiddleware(BaseMiddleware):
    def __init__(self, admin_target: str):
        super().__init__()
        self.admin_target = admin_target.strip()
        self.clean_target = self.admin_target.lstrip("@").lower()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return None

        user_username = (user.username or "").lower()
        user_id_str = str(user.id)

        is_authorized = False
        if user_username and user_username == self.clean_target:
            is_authorized = True
        elif user_id_str == self.clean_target:
            is_authorized = True

        if not is_authorized:
            logger.warning(
                f"Unauthorized access rejected: id={user.id}, username=@{user.username}, name='{user.full_name}'"
            )
            if isinstance(event, Message):
                await event.answer(
                    "⛔ <b>Доступ запрещен.</b>\nУ вас нет прав для управления данным сервером.",
                    parse_mode="HTML",
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещен.", show_alert=True)
            return None

        return await handler(event, data)
