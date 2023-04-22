import asyncio

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.db import check_connection
from middlewares.db import DbSessionMiddleware
from config_reader import config
from handlers import setup_routers


async def main():
    engine = create_async_engine(url=config.SQLALCHEMY_DATABASE_URI, echo=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    # инициализируем бот и диспетчер
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    router = setup_routers()
    dp.include_router(router)
    # Проверяем подключение к БД
    await check_connection()
    # Запуск поллинга
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
