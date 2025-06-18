import asyncio, logging, asyncpg
from aiogram import Bot, Dispatcher
from .settings import settings
from .handlers import register_handlers


async def main():
    bot = Bot(settings.tg_token)
    dp  = Dispatcher()
    db  = await asyncpg.create_pool(dsn=settings.db_dsn)

    register_handlers(dp, db)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
