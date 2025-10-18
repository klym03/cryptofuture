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
    
    # Перевіряємо чи є реферальний код в команді /start
    referral_code = None
    is_admin_referral = False
    is_user_referral = False
    
    if message.get_args():
        potential_code = message.get_args().strip()
        
        # Спочатку перевіряємо чи це адмінське посилання
        referral_link = await db.get_referral_link(potential_code)
        if referral_link:
            referral_code = potential_code
            is_admin_referral = True
            # Додаємо статистику про перехід
            await db.add_referral_stat(referral_code, user_id, 'click')
        else:
            # Якщо не адмінське, перевіряємо чи це користувацьке посилання
            # Користувацькі коди мають формат U{user_id}_{random}
            user_by_ref = await db.get_user_by_referral_code(potential_code)
            if user_by_ref:
                referral_code = potential_code
                is_user_referral = True

    # Перевіряємо чи користувач вже існує
    existing_user = await db.get_user(user_id)
    
    if not existing_user:
        # Новий користувач - додаємо з реферальним кодом (якщо є)
        await db.add_user(user_id, username, first_name, referral_code)
        
        # Якщо прийшов по реферальному посиланню, додаємо статистику реєстрації
        if referral_code and is_admin_referral:
            await db.add_referral_stat(referral_code, user_id, 'register')
    else:
        # Існуючий користувач - просто оновлюємо дані
        await db.add_user(user_id, username, first_name)

    # Формуємо привітальне повідомлення
    welcome_text = f"👋 Привіт, {first_name}!\n\n"
    
    if not existing_user and referral_code:
        # Новий користувач прийшов по реферальному посиланню
        if is_user_referral:
            welcome_text += "🎉 Вітаємо! Ви приєдналися через запрошення від друга.\n\n"
        else:
            welcome_text += "🎉 Вітаємо! Ви приєдналися через реферальне посилання.\n\n"
    
    welcome_text += (
        "Я ваш особистий AI-помічник для аналізу ф'ючерсних угод. "
        "Надішліть мені фотографію графіка, і я надам технічний аналіз та торгову ідею.\n\n"
        "У вас є <b>3 безкоштовні спроби</b>, щоб оцінити мої можливості."
    )

    await message.answer(
        welcome_text,
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


async def cmd_my_referrals(message: types.Message):
    """Обробник команди /my_referals"""
    user_id = message.from_user.id
    
    # Отримуємо статистику
    stats = await db.get_user_referral_stats(user_id)
    
    # Перевіряємо чи є у користувача реферальне посилання
    if not stats['has_referral_link']:
        await message.answer(
            "🔗 <b>Реферальна програма</b>\n\n"
            "❌ У вас ще немає реферального посилання.\n\n"
            "💡 <b>Як отримати посилання:</b>\n"
            "Зверніться до нашого менеджера @nin_0009 для створення вашого персонального реферального посилання.\n\n"
            "🎁 <b>Переваги реферальної програми:</b>\n"
            "▫️ Отримуйте винагороди за запрошених друзів\n"
            "▫️ Відстежуйте статистику рефералів\n"
            "▫️ Мотивуйте друзів оформити підписку",
            parse_mode="HTML"
        )
        return
    
    # Отримуємо список рефералів
    referrals = await db.get_user_referrals(user_id)
    
    # Формуємо посилання
    bot_info = await message.bot.get_me()
    referral_url = f"https://t.me/{bot_info.username}?start={stats['referral_code']}"
    
    # Формуємо текст відповіді
    response = f"🔗 <b>Ваша реферальна програма</b>\n\n"
    response += f"📝 <b>Назва:</b> {stats['referral_name']}\n\n"
    response += f"📊 <b>Статистика:</b>\n"
    response += f"👥 Всього рефералів: <b>{stats['total_referrals']}</b>\n"
    response += f"💎 З підпискою: <b>{stats['subscribed_referrals']}</b>\n\n"
    
    response += f"🌐 <b>Ваше реферальне посилання:</b>\n"
    response += f"<code>{referral_url}</code>\n\n"
    
    if referrals:
        response += f"👥 <b>Ваші реферали ({len(referrals)}):</b>\n\n"
        for i, ref in enumerate(referrals[:10], 1):  # Показуємо перших 10
            username_display = f"@{ref['username']}" if ref['username'] else ref['first_name']
            subscription_status = "💎" if ref['is_subscribed'] else "👤"
            date_str = ref['created_at'].strftime('%d.%m.%Y')
            response += f"{i}. {subscription_status} {username_display} ({date_str})\n"
        
        if len(referrals) > 10:
            response += f"\n<i>... та ще {len(referrals) - 10}</i>\n"
    else:
        response += f"📝 У вас поки немає рефералів.\n"
        response += f"Поділіться посиланням, щоб запросити друзів!"
    
    await message.answer(response, parse_mode="HTML")


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(cmd_profile, text="👤 Профіль")
    dp.register_message_handler(cmd_trade, text="💡 Допомога з угодою")
    dp.register_message_handler(cmd_my_referrals, commands=["my_referals"]) 