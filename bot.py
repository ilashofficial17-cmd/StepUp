import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN, DB_PATH
from database.db import init_db
from database.storage import SQLiteStorage
from handlers import admin, courses, learning, onboarding, start


async def main():
    logging.basicConfig(level=logging.INFO)

    await init_db()
    storage = SQLiteStorage(DB_PATH)
    await storage.init()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # learning — первым: перехватывает сообщения во время урока
    # (включая /start и /menu, чтобы корректно сбросить состояние)
    dp.include_router(learning.router)
    # onboarding — до общих обработчиков: перехватывает ответы диагностики
    dp.include_router(onboarding.router)
    # admin — до общих, чтобы /grant / /whoami работали из любого места
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(courses.router)

    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
