import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from config import BOT_TOKEN
from bot.handlers.user_handlers import register_user_handlers
from bot.handlers.trade_handlers import register_trade_handlers
from bot.handlers.payment_handlers import register_payment_handlers
from bot.handlers.admin_handlers import register_admin_handlers
from db import queries as db

# Встановлюємо рівень логування
logging.basicConfig(level=logging.INFO)

# Ініціалізуємо бота та диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(dp):
    """Виконується при старті бота"""
    logging.info("Створення підключення до PostgreSQL...")
    await db.create_pool()
    logging.info("Створення таблиць (якщо не існують)...")
    await db.create_tables()


async def on_shutdown(dp):
    """Виконується при зупинці бота"""
    logging.info("Закриття підключення до PostgreSQL...")
    await db.close_pool()


if __name__ == "__main__":
    register_user_handlers(dp)
    register_trade_handlers(dp)
    register_payment_handlers(dp)
    register_admin_handlers(dp)

    executor.start_polling(
        dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown
    )
