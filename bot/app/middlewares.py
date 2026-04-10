from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Union

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        user_info = f"{user.first_name} (id={user.id})" if user else "unknown"

        if isinstance(event, Message):
            logger.info("Message from %s: %s", user_info, event.text or "(no text)")
        elif isinstance(event, CallbackQuery):
            logger.info("Callback from %s: %s", user_info, event.data)

        return await handler(event, data)
