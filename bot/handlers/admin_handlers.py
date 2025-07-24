from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from config import ADMIN_ID
from db import queries as db


async def cmd_test_payment(message: types.Message):
    """
    A secret admin command to simulate a successful payment and activate a subscription.
    """
    if str(message.from_user.id) != ADMIN_ID:
        return

    user_id = message.from_user.id
    await db.activate_subscription(user_id)
    
    await message.bot.send_message(user_id, "✅ Тестову підписку успішно активовано на 30 днів.")


async def cmd_reset_subscription(message: types.Message):
    """
    A secret admin command to reset subscription status.
    """
    if str(message.from_user.id) != ADMIN_ID:
        return

    user_id = message.from_user.id
    await db.update_subscription_status(user_id, False)
    
    await message.bot.send_message(user_id, "✅ Підписку скинуто для тестування.")


def register_admin_handlers(dp):
    dp.register_message_handler(cmd_test_payment, Command("test_payment"))
    dp.register_message_handler(cmd_reset_subscription, Command("reset_subscription")) 