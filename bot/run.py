import asyncio

from aiogram import Bot, Dispatcher

from config_reader import config


async def main():
    # инициализируем бот и диспетчер
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    dp = Dispatcher()
    # Запуск поллинга
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
