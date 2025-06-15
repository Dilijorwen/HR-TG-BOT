import asyncio, logging, asyncpg
from aiogram import Bot, Dispatcher
from .settings import settings
from .handlers import register_handlers

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(settings.tg_token)
    dp  = Dispatcher()
    db  = await asyncpg.create_pool(dsn=settings.db_dsn)

    register_handlers(dp, db)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
