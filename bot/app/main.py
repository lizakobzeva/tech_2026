import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers import router as handlers_router
from app.middlewares import LoggingMiddleware
from app.http_requests import backend_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    dp.include_router(handlers_router)

    logger.info("Starting DatingBot...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await backend_client.close()


if __name__ == "__main__":
    asyncio.run(main())
