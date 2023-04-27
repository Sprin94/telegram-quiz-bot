import asyncio

from aiogram import Bot, Dispatcher

from database.db import check_connection, sessionmaker
from middlewares.db import DbSessionMiddleware
from config_reader import config
from handlers import setup_routers
from services.create_poll import create_quizzes_tasks


async def main():
    # инициализируем бот и диспетчер
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    router = setup_routers()
    dp.include_router(router)
    # Проверяем подключение к БД
    await check_connection()
    # Создаем ежедневные опросы, если они запланированы
    await create_quizzes_tasks(bot)
    # Запуск поллинга
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())
