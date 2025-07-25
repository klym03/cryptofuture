from aiogram import Dispatcher, types
from db import queries as db
from bot.keyboards.reply import main_menu_keyboard, subscribe_keyboard
from datetime import datetime, timezone
from typing import Union


async def get_profile_data(user_id: int):
    """Готує текст та клавіатуру для повідомлення профілю."""
    user = await db.get_user(user_id)
    if not user:
        return "Я не можу знайти ваш профіль. Будь ласка, натисніть /start, щоб зареєструватися.", None

    current_time = datetime.now(timezone.utc)
    is_subscribed = user["is_subscribed"]
    subscription_expires_at = user["subscription_expires_at"]

    # Якщо з бази приходить дата без часової зони, робимо її aware (UTC)
    if subscription_expires_at and subscription_expires_at.tzinfo is None:
        subscription_expires_at = subscription_expires_at.replace(tzinfo=timezone.utc)

    if is_subscribed and subscription_expires_at and subscription_expires_at < current_time:
        is_subscribed = False
        await db.update_subscription_status(user["user_id"], False)

    if is_subscribed and subscription_expires_at:
        subscription_status = "✅ Активна"
        expires_text = f"<b>Діє до:</b> {subscription_expires_at.strftime('%d.%m.%Y %H:%M')} UTC"
    else:
        subscription_status = "❌ Неактивна"
        expires_text = ""

    profile_text = f"👤 <b>Ваш профіль:</b>\n\n"
    profile_text += f"<b>ID:</b> <code>{user['user_id']}</code>\n"
    profile_text += f"<b>Ім'я:</b> {user['first_name']}\n"
    if user['username']:
        profile_text += f"<b>Username:</b> @{user['username']}\n"
    profile_text += f"\n📊 <b>Статистика:</b>\n"
    profile_text += f"<b>Безкоштовних угод:</b> {user['free_trades_left']}\n"
    profile_text += f"<b>Підписка:</b> {subscription_status}\n"
    if expires_text:
        profile_text += f"{expires_text}\n"

    if is_subscribed:
        profile_text += f"\n🎯 <b>Ваші можливості:</b>\n"
        profile_text += f"▫️ Необмежена кількість аналізів\n"
        profile_text += f"▫️ Детальні торгові рекомендації\n"
        profile_text += f"▫️ Рівні входу, стоп-лосс та тейк-профіт\n"
        profile_text += f"▫️ Рекомендації по плечу\n"
    else:
        profile_text += f"\n💡 <b>Доступно з підпискою:</b>\n"
        profile_text += f"▫️ Необмежена кількість аналізів\n"
        profile_text += f"▫️ Детальні торгові рекомендації\n"
        profile_text += f"▫️ Рівні входу, стоп-лосс та тейк-профіт\n"
        profile_text += f"▫️ Рекомендації по плечу\n"

    keyboard = subscribe_keyboard if not is_subscribed else None
    return profile_text, keyboard


async def cmd_start(message: types.Message):
    """Обробник команди /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Додаємо користувача, якщо він новий. ON CONFLICT в SQL подбає про дублікати.
    await db.add_user(user_id, username, first_name)

    await message.answer(
        f"👋 Привіт, {first_name}!\n\n"
        "Я ваш особистий AI-помічник для аналізу ф'ючерсних угод. "
        "Надішліть мені фотографію графіка, і я надам технічний аналіз та торгову ідею.\n\n"
        "У вас є <b>1 безкоштовна спроба</b>, щоб оцінити мої можливості.",
        reply_markup=main_menu_keyboard,
        parse_mode="HTML",
    )


async def show_profile(message_or_callback: Union[types.Message, types.CallbackQuery]):
    """Показує профіль користувача, редагуючи повідомлення, якщо це callback."""
    user_id = message_or_callback.from_user.id
    profile_text, keyboard = await get_profile_data(user_id)

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(
            profile_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    elif isinstance(message_or_callback, types.CallbackQuery):
        # Використовуємо message з callback, щоб знати, яке повідомлення редагувати
        await message_or_callback.message.edit_text(
            profile_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await message_or_callback.answer()


async def cmd_profile(message: types.Message):
    """Обробник команди 'Профіль'"""
    await show_profile(message)


async def cmd_trade(message: types.Message):
    """Обробник команди 'Допомога з угодою'"""
    await message.answer(
        "Привіт! Я готовий допомогти вам з угодою.\n\n"
        "Будь ласка, відправте мені фотографію або скріншот графіку. "
        "Переконайтеся, що на зображенні чітко видно:\n"
        "- Назву монети\n"
        "- Таймфрейм\n"
        "- Індикатори, які ви використовуєте (якщо є)\n\n"
        "Я проаналізую графік і запропоную найкращий варіант для угоди."
    )


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(cmd_profile, text="👤 Профіль")
    dp.register_message_handler(cmd_trade, text="💡 Допомога з угодою") 