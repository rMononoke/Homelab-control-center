import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers import router
from middlewares import AuthMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bot")


async def main():
    logger.info("Starting Homelab Telegram Bot Gateway...")
    logger.info(f"Admin configured as: {settings.admin_identifier}")
    logger.info(f"Targeting Core API at: {settings.CORE_API_URL}")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register Auth Middleware on both messages and callback queries
    auth_middleware = AuthMiddleware(admin_target=settings.admin_identifier)
    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)

    # Register handlers
    dp.include_router(router)

    # Delete webhook if previously set to ensure polling works cleanly
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())