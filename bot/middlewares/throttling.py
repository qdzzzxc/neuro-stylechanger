from typing import Any, Awaitable, Callable, Dict
import logging

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    caches = TTLCache(maxsize=10_000, ttl=15)

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        if event.chat.id in self.caches and self.caches[event.chat.id] == 4:
            logging.info(
                f'Пользователь {event.from_user.username} с id {event.from_user.id} был остановлен спам фильтром')
            await event.reply(text='Не спамьте, подождите 15 секунд')
            return
        else:
            if event.chat.id in self.caches:
                self.caches[event.chat.id] += 1
            else:
                self.caches[event.chat.id] = 0
        return await handler(event, data)