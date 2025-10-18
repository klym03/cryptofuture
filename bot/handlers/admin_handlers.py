from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.utils.exceptions import MessageNotModified
import logging

from config import ADMIN_ID
from db import queries as db
from bot.keyboards.reply import (
    admin_main_keyboard, admin_users_keyboard, admin_referrals_keyboard,
    admin_referral_navigation_keyboard, admin_referral_detail_keyboard
)
from bot.states import AdminStates


def is_admin(user_id: int) -> bool:
    """Перевіряє чи є користувач адміністратором"""
    return str(user_id) == ADMIN_ID


# =============== ОСНОВНІ АДМІН КОМАНДИ ===============

async def cmd_admin(message: types.Message):
    """Команда /admin - відкриває адмін панель"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🔧 <b>Панель адміністратора</b>\n\n"
        "Оберіть розділ для управління:",
        reply_markup=admin_main_keyboard
    )


async def callback_admin_main(callback: types.CallbackQuery):
    """Повернення до головної адмін панелі"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    try:
        await callback.message.edit_text(
            "🔧 <b>Панель адміністратора</b>\n\n"
            "Оберіть розділ для управління:",
            reply_markup=admin_main_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


# =============== УПРАВЛІННЯ КОРИСТУВАЧАМИ ===============

async def callback_admin_users(callback: types.CallbackQuery):
    """Відкриває розділ управління користувачами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    try:
        await callback.message.edit_text(
            "👤 <b>Управління користувачами</b>\n\n"
            "Оберіть дію:",
            reply_markup=admin_users_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def callback_admin_grant_subscription(callback: types.CallbackQuery, state: FSMContext):
    """Почати процес надання підписки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    await AdminStates.waiting_for_grant_subscription_user.set()
    try:
        await callback.message.edit_text(
            "💎 <b>Надання підписки</b>\n\n"
            "Введіть username користувача (без @) або user_id:",
            reply_markup=admin_users_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def process_grant_subscription(message: types.Message, state: FSMContext):
    """Обробка надання підписки"""
    if not is_admin(message.from_user.id):
        return
    
    user_input = message.text.strip()
    target_user = None
    
    # Спробуємо знайти користувача за username або user_id
    if user_input.isdigit():
        target_user = await db.get_user(int(user_input))
    else:
        target_user = await db.get_user_by_username(user_input)
    
    if not target_user:
        await message.answer(
            "❌ Користувача не знайдено!\n\n"
            "Перевірте правильність введених даних.",
            reply_markup=admin_users_keyboard
        )
        await state.finish()
        return
    
    # Надаємо підписку
    await db.admin_grant_subscription(target_user['user_id'])
    
    username_display = f"@{target_user['username']}" if target_user['username'] else f"ID: {target_user['user_id']}"
    await message.answer(
        f"✅ <b>Підписку надано!</b>\n\n"
        f"👤 Користувач: {username_display}\n"
        f"📛 Ім'я: {target_user['first_name']}\n"
        f"💎 Підписка: активна на 30 днів",
        reply_markup=admin_users_keyboard
    )
    
    # Повідомляємо користувача
    try:
        await message.bot.send_message(
            target_user['user_id'],
            "🎉 <b>Вітаємо!</b>\n\n"
            "Вам було надано підписку на 30 днів!\n"
            "Тепер у вас є необмежений доступ до аналізу угод."
        )
    except:
        pass  # Користувач заблокував бота
    
    await state.finish()


async def callback_admin_grant_tries(callback: types.CallbackQuery, state: FSMContext):
    """Почати процес надання безкоштовних спроб"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    await AdminStates.waiting_for_grant_tries_user.set()
    try:
        await callback.message.edit_text(
            "🎁 <b>Надання безкоштовних спроб</b>\n\n"
            "Введіть username користувача (без @) або user_id:",
            reply_markup=admin_users_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def process_grant_tries(message: types.Message, state: FSMContext):
    """Обробка надання безкоштовних спроб"""
    if not is_admin(message.from_user.id):
        return
    
    user_input = message.text.strip()
    target_user = None
    
    # Спробуємо знайти користувача за username або user_id
    if user_input.isdigit():
        target_user = await db.get_user(int(user_input))
    else:
        target_user = await db.get_user_by_username(user_input)
    
    if not target_user:
        await message.answer(
            "❌ Користувача не знайдено!\n\n"
            "Перевірте правильність введених даних.",
            reply_markup=admin_users_keyboard
        )
        await state.finish()
        return
    
    # Надаємо одну безкоштовну спробу
    await db.admin_grant_free_tries(target_user['user_id'], 1)
    
    username_display = f"@{target_user['username']}" if target_user['username'] else f"ID: {target_user['user_id']}"
    await message.answer(
        f"✅ <b>Безкоштовну спробу надано!</b>\n\n"
        f"👤 Користувач: {username_display}\n"
        f"📛 Ім'я: {target_user['first_name']}\n"
        f"🎁 Додано: 1 безкоштовна спроба",
        reply_markup=admin_users_keyboard
    )
    
    # Повідомляємо користувача
    try:
        await message.bot.send_message(
            target_user['user_id'],
            "🎉 <b>Вітаємо!</b>\n\n"
            "Вам було надано 1 безкоштовну спробу!\n"
            "Тепер ви можете скористатися аналізом угод."
        )
    except:
        pass  # Користувач заблокував бота
    
    await state.finish()


async def callback_admin_search_user(callback: types.CallbackQuery, state: FSMContext):
    """Пошук користувача"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    await AdminStates.waiting_for_user_search.set()
    try:
        await callback.message.edit_text(
            "🔍 <b>Пошук користувача</b>\n\n"
            "Введіть частину username або імені для пошуку:",
            reply_markup=admin_users_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def process_user_search(message: types.Message, state: FSMContext):
    """Обробка пошуку користувачів"""
    if not is_admin(message.from_user.id):
        return
    
    query = message.text.strip()
    users = await db.search_users(query, limit=10)
    
    if not users:
        await message.answer(
            "❌ Користувачів не знайдено!\n\n"
            "Спробуйте інший запит.",
            reply_markup=admin_users_keyboard
        )
        await state.finish()
        return
    
    # Формуємо список знайдених користувачів
    result_text = "🔍 <b>Результати пошуку:</b>\n\n"
    for user in users:
        username_display = f"@{user['username']}" if user['username'] else "немає"
        subscription_status = "💎 Активна" if user['is_subscribed'] else "❌ Неактивна"
        
        result_text += (
            f"👤 <b>{user['first_name']}</b>\n"
            f"🆔 ID: <code>{user['user_id']}</code>\n"
            f"👤 Username: {username_display}\n"
            f"💎 Підписка: {subscription_status}\n"
            f"🎁 Спроби: {user['free_trades_left']}\n\n"
        )
    
    await message.answer(result_text, reply_markup=admin_users_keyboard)
    await state.finish()


# =============== РЕФЕРАЛЬНІ ПОСИЛАННЯ ===============

async def callback_admin_referrals(callback: types.CallbackQuery):
    """Відкриває розділ реферальних посилань"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    try:
        await callback.message.edit_text(
            "🔗 <b>Реферальні посилання</b>\n\n"
            "Оберіть дію:",
            reply_markup=admin_referrals_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def callback_admin_create_referral(callback: types.CallbackQuery, state: FSMContext):
    """Почати створення реферального посилання"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    await AdminStates.waiting_for_referral_name.set()
    try:
        await callback.message.edit_text(
            "➕ <b>Створення реферального посилання</b>\n\n"
            "Введіть назву для нового посилання:",
            reply_markup=admin_referrals_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def process_create_referral(message: types.Message, state: FSMContext):
    """Обробка створення реферального посилання - етап 1: назва"""
    if not is_admin(message.from_user.id):
        return
    
    referral_name = message.text.strip()
    
    if len(referral_name) < 3:
        await message.answer(
            "❌ Назва занадто коротка!\n\n"
            "Мінімум 3 символи.",
            reply_markup=admin_referrals_keyboard
        )
        await state.finish()
        return
    
    # Зберігаємо назву в стан
    await state.update_data(referral_name=referral_name)
    
    # Переходимо до вибору власника
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Прив'язати до користувача", callback_data="ref_bind_user")],
        [InlineKeyboardButton(text="🌐 Звичайне посилання", callback_data="ref_no_bind")],
        [InlineKeyboardButton(text="🔙 Скасувати", callback_data="admin_referrals")]
    ])
    
    await AdminStates.waiting_for_referral_owner.set()
    await message.answer(
        f"📝 <b>Назва:</b> {referral_name}\n\n"
        f"❓ <b>Тип посилання:</b>\n"
        f"Оберіть, чи потрібно прив'язати посилання до конкретного користувача:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def callback_ref_bind_user(callback: types.CallbackQuery, state: FSMContext):
    """Обробка вибору прив'язки до користувача"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    await callback.message.edit_text(
        "👤 <b>Прив'язка до користувача</b>\n\n"
        "Введіть username користувача (без @) або user_id:",
        parse_mode="HTML"
    )
    await callback.answer()


async def callback_ref_no_bind(callback: types.CallbackQuery, state: FSMContext):
    """Обробка створення звичайного посилання"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    # Отримуємо назву зі стану
    data = await state.get_data()
    referral_name = data.get('referral_name')
    
    # Створюємо звичайне посилання (без owner_user_id)
    referral_code = await db.create_referral_link(callback.from_user.id, referral_name)
    bot_username = (await callback.bot.get_me()).username
    referral_url = f"https://t.me/{bot_username}?start={referral_code}"
    
    await callback.message.edit_text(
        f"✅ <b>Звичайне реферальне посилання створено!</b>\n\n"
        f"📝 Назва: {referral_name}\n"
        f"🔗 Код: <code>{referral_code}</code>\n"
        f"🌐 Посилання: <code>{referral_url}</code>\n\n"
        f"Скопіюйте посилання та поширюйте!",
        reply_markup=admin_referrals_keyboard,
        parse_mode="HTML"
    )
    await state.finish()
    await callback.answer()


async def process_referral_owner(message: types.Message, state: FSMContext):
    """Обробка вибору власника реферального посилання"""
    if not is_admin(message.from_user.id):
        return
    
    user_input = message.text.strip()
    target_user = None
    
    # Спробуємо знайти користувача за username або user_id
    if user_input.isdigit():
        target_user = await db.get_user(int(user_input))
    else:
        target_user = await db.get_user_by_username(user_input)
    
    if not target_user:
        await message.answer(
            "❌ Користувача не знайдено!\n\n"
            "Перевірте правильність введених даних.",
            reply_markup=admin_referrals_keyboard
        )
        await state.finish()
        return
    
    # Отримуємо назву зі стану
    data = await state.get_data()
    referral_name = data.get('referral_name')
    
    # Створюємо посилання прив'язане до користувача
    referral_code = await db.create_referral_link(
        message.from_user.id, 
        referral_name,
        owner_user_id=target_user['user_id']
    )
    bot_username = (await message.bot.get_me()).username
    referral_url = f"https://t.me/{bot_username}?start={referral_code}"
    
    username_display = f"@{target_user['username']}" if target_user['username'] else f"ID: {target_user['user_id']}"
    
    await message.answer(
        f"✅ <b>Персональне реферальне посилання створено!</b>\n\n"
        f"📝 Назва: {referral_name}\n"
        f"👤 Власник: {username_display} ({target_user['first_name']})\n"
        f"🔗 Код: <code>{referral_code}</code>\n"
        f"🌐 Посилання: <code>{referral_url}</code>\n\n"
        f"💡 Користувач зможе переглядати своїх рефералів через команду /my_referals",
        reply_markup=admin_referrals_keyboard
    )
    
    # Повідомляємо користувача
    try:
        await message.bot.send_message(
            target_user['user_id'],
            f"🎉 <b>Вітаємо!</b>\n\n"
            f"Для вас створено персональне реферальне посилання!\n\n"
            f"📝 Назва: {referral_name}\n"
            f"🔗 Ваше посилання: <code>{referral_url}</code>\n\n"
            f"Використовуйте команду /my_referals для перегляду статистики."
        )
    except:
        pass  # Користувач заблокував бота
    
    await state.finish()


async def callback_admin_list_referrals(callback: types.CallbackQuery):
    """Показати список реферальних посилань"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    links = await db.get_admin_referral_links(callback.from_user.id)
    
    if not links:
        try:
            await callback.message.edit_text(
                "📋 <b>Список реферальних посилань</b>\n\n"
                "У вас ще немає створених посилань.\n"
                "Створіть перше посилання!",
                reply_markup=admin_referrals_keyboard
            )
        except MessageNotModified:
            pass
        await callback.answer()
        return
    
    # Показуємо список з навігацією
    keyboard = admin_referral_navigation_keyboard(links, page=0)
    try:
        await callback.message.edit_text(
            "📋 <b>Список реферальних посилань</b>\n\n"
            f"Всього посилань: {len(links)}\n"
            "🟢 - активне, 🔴 - неактивне\n"
            "👥 - реєстрації, 💎 - підписки",
            reply_markup=keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def callback_admin_referral_detail(callback: types.CallbackQuery):
    """Показати детальну інформацію про реферальне посилання"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    # Отримуємо код з callback_data
    referral_code = callback.data.split("_")[-1]
    
    # Отримуємо інформацію про посилання
    link = await db.get_referral_link(referral_code)
    if not link:
        await callback.answer("❌ Посилання не знайдено")
        return
    
    bot_username = (await callback.bot.get_me()).username
    referral_url = f"https://t.me/{bot_username}?start={referral_code}"
    
    status_text = "🟢 Активне" if link['is_active'] else "🔴 Неактивне"
    
    # Отримуємо статистику
    links = await db.get_admin_referral_links(callback.from_user.id)
    current_link = next((l for l in links if l['code'] == referral_code), None)
    
    if current_link:
        registrations = current_link['registrations']
        subscriptions = current_link['subscriptions']
    else:
        registrations = subscriptions = 0
    
    try:
        await callback.message.edit_text(
            f"🔗 <b>Деталі реферального посилання</b>\n\n"
            f"📝 Назва: {link['name']}\n"
            f"🔗 Код: <code>{referral_code}</code>\n"
            f"📊 Статус: {status_text}\n"
            f"👥 Реєстрації: {registrations}\n"
            f"💎 Підписки: {subscriptions}\n"
            f"📅 Створено: {link['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🌐 Посилання:\n<code>{referral_url}</code>",
            reply_markup=admin_referral_detail_keyboard(referral_code, link['is_active'])
        )
    except MessageNotModified:
        pass
    await callback.answer()


async def callback_admin_toggle_referral(callback: types.CallbackQuery):
    """Змінити статус реферального посилання"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    referral_code = callback.data.split("_")[-1]
    await db.toggle_referral_link_status(referral_code, callback.from_user.id)
    
    # Повертаємо до деталей посилання
    await callback_admin_referral_detail(callback)


async def callback_admin_copy_referral(callback: types.CallbackQuery):
    """Копіювати реферальне посилання"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    referral_code = callback.data.split("_")[-1]
    bot_username = (await callback.bot.get_me()).username
    referral_url = f"https://t.me/{bot_username}?start={referral_code}"
    
    await callback.answer(f"📋 Посилання скопійовано:\n{referral_url}", show_alert=True)


async def callback_admin_referral_stats(callback: types.CallbackQuery):
    """Показати загальну статистику реферальних посилань"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    stats = await db.get_referral_stats_summary(callback.from_user.id)
    
    try:
        await callback.message.edit_text(
            f"📈 <b>Загальна статистика</b>\n\n"
            f"🔗 Всього посилань: {stats['total_links']}\n"
            f"👥 Всього реєстрацій: {stats['total_registrations']}\n"
            f"💎 Всього підписок: {stats['total_subscriptions']}\n\n"
            f"📊 Конверсія в підписку: "
            f"{(stats['total_subscriptions'] / max(stats['total_registrations'], 1) * 100):.1f}%",
            reply_markup=admin_referrals_keyboard
        )
    except MessageNotModified:
        pass
    await callback.answer()


# =============== СТАТИСТИКА ===============

async def callback_admin_stats(callback: types.CallbackQuery):
    """Показати загальну статистику бота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено")
        return
    
    try:
        # Отримуємо загальну статистику
        stats = await db.get_bot_stats()
        
        # Розраховуємо конверсію
        conversion_rate = 0
        if stats['total_referral_clicks'] > 0:
            conversion_rate = (stats['referral_subscriptions'] / stats['total_referral_clicks']) * 100
        
        await callback.message.edit_text(
            f"📊 <b>Загальна статистика бота</b>\n\n"
            f"👥 <b>Користувачі:</b>\n"
            f"• Всього: {stats['total_users']}\n"
            f"• За останні 7 днів: {stats['recent_users']}\n\n"
            f"💎 <b>Підписки:</b>\n"
            f"• Активні: {stats['active_subscriptions']}\n"
            f"• Через реферали: {stats['referral_subscriptions']}\n\n"
            f"🔗 <b>Реферальна система:</b>\n"
            f"• Всього посилань: {stats['total_referral_links']}\n"
            f"• Реєстрації: {stats['total_referral_clicks']}\n"
            f"• Конверсія: {conversion_rate:.1f}%\n\n"
            f"📈 <b>Ефективність:</b>\n"
            f"• Підписок на користувача: {(stats['active_subscriptions'] / max(stats['total_users'], 1) * 100):.1f}%",
            reply_markup=admin_main_keyboard
        )
    except MessageNotModified:
        pass
    except Exception as e:
        logging.error(f"Помилка отримання статистики: {e}")
        await callback.message.edit_text(
            "📊 <b>Загальна статистика</b>\n\n"
            "❌ Помилка завантаження статистики\n"
            "Спробуйте пізніше",
            reply_markup=admin_main_keyboard
        )
    
    await callback.answer()


# =============== СТАРІ КОМАНДИ (для сумісності) ===============

async def cmd_test_payment(message: types.Message):
    """Тестова команда для активації підписки"""
    if not is_admin(message.from_user.id):
        return

    user_id = message.from_user.id
    await db.activate_subscription(user_id)
    
    await message.answer("✅ Тестову підписку успішно активовано на 30 днів.")


async def cmd_reset_subscription(message: types.Message):
    """Тестова команда для скидання підписки"""
    if not is_admin(message.from_user.id):
        return

    user_id = message.from_user.id
    await db.update_subscription_status(user_id, False)
    
    await message.answer("✅ Підписку скинуто для тестування.")


# =============== РЕЄСТРАЦІЯ ХЕНДЛЕРІВ ===============

def register_admin_handlers(dp):
    # Команди
    dp.register_message_handler(cmd_admin, Command("admin"))
    dp.register_message_handler(cmd_test_payment, Command("test_payment"))
    dp.register_message_handler(cmd_reset_subscription, Command("reset_subscription")) 
    
    # Callback кнопки - головне меню
    dp.register_callback_query_handler(callback_admin_main, Text("admin_main"))
    dp.register_callback_query_handler(callback_admin_users, Text("admin_users"))
    dp.register_callback_query_handler(callback_admin_referrals, Text("admin_referrals"))
    dp.register_callback_query_handler(callback_admin_stats, Text("admin_stats"))
    
    # Callback кнопки - користувачі
    dp.register_callback_query_handler(callback_admin_grant_subscription, Text("admin_grant_subscription"))
    dp.register_callback_query_handler(callback_admin_grant_tries, Text("admin_grant_tries"))
    dp.register_callback_query_handler(callback_admin_search_user, Text("admin_search_user"))
    
    # Callback кнопки - реферальні посилання
    dp.register_callback_query_handler(callback_admin_create_referral, Text("admin_create_referral"))
    dp.register_callback_query_handler(callback_admin_list_referrals, Text("admin_list_referrals"))
    dp.register_callback_query_handler(callback_admin_referral_stats, Text("admin_referral_stats"))
    dp.register_callback_query_handler(callback_admin_referral_detail, Text(startswith="admin_referral_detail_"))
    dp.register_callback_query_handler(callback_admin_toggle_referral, Text(startswith="admin_toggle_referral_"))
    dp.register_callback_query_handler(callback_admin_copy_referral, Text(startswith="admin_copy_referral_"))
    
    # Callback для створення реферальних посилань
    dp.register_callback_query_handler(callback_ref_bind_user, Text("ref_bind_user"), state=AdminStates.waiting_for_referral_owner)
    dp.register_callback_query_handler(callback_ref_no_bind, Text("ref_no_bind"), state=AdminStates.waiting_for_referral_owner)
    
    # Обробка станів
    dp.register_message_handler(process_grant_subscription, state=AdminStates.waiting_for_grant_subscription_user)
    dp.register_message_handler(process_grant_tries, state=AdminStates.waiting_for_grant_tries_user)
    dp.register_message_handler(process_user_search, state=AdminStates.waiting_for_user_search)
    dp.register_message_handler(process_create_referral, state=AdminStates.waiting_for_referral_name)
    dp.register_message_handler(process_referral_owner, state=AdminStates.waiting_for_referral_owner) 