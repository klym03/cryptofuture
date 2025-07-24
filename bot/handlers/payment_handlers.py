from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from db import queries as db
import logging
from datetime import datetime, timedelta
from bot.handlers.user_handlers import show_profile

# Ціна підписки в Telegram Stars
PRICE = types.LabeledPrice(label="Підписка на 30 днів", amount=250)  # Ціна в XTR

async def handle_subscribe(callback_query: types.CallbackQuery):
    """Обробляє натискання кнопки підписки"""
    user_id = callback_query.from_user.id
    
    try:
        # Створюємо інвойс для оплати через Telegram Stars
        await callback_query.bot.send_invoice(
            chat_id=user_id,
            title="Підписка на AI аналіз угод",
            description="Отримайте необмежений доступ до AI аналізу торгових графіків на 30 днів",
            payload=f"subscription_{user_id}",
            provider_token="",  # Порожній для Telegram Stars
            currency="XTR",  # Telegram Stars
            prices=[PRICE],
            start_parameter="subscribe",
        )
        
        await callback_query.answer("Інвойс для оплати надіслано. Натисніть 'Оплатити', щоб продовжити.", show_alert=True)
        
    except Exception as e:
        logging.error(f"Помилка створення інвойсу: {e}")
        await callback_query.answer("❌ Помилка створення платежу. Спробуйте пізніше.", show_alert=True)

async def handle_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Обробляє запит перед оплатою"""
    try:
        # Перевіряємо валідність платежу
        if pre_checkout_query.invoice_payload.startswith("subscription_"):
            await pre_checkout_query.bot.answer_pre_checkout_query(
                pre_checkout_query.id, 
                ok=True
            )
        else:
            await pre_checkout_query.bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="Невірний тип платежу"
            )
    except Exception as e:
        logging.error(f"Помилка pre-checkout: {e}")
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Помилка обробки платежу"
        )

async def handle_successful_payment(message: types.Message):
    """Обробляє успішний платіж"""
    user_id = message.from_user.id
    payment = message.successful_payment
    
    try:
        # Активуємо підписку на 30 днів
        await db.activate_subscription(user_id, days=30)
        
        logging.info(f"Підписка активована для користувача {user_id}")
        
        await message.answer(
            "🎉 <b>Підписка успішно активована!</b>\n\n"
            "✅ Тепер у вас є необмежений доступ до AI аналізу торгових графіків на 30 днів.\n\n"
            "📊 Надсилайте скріншоти графіків і отримуйте детальний технічний аналіз!",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logging.error(f"Помилка активації підписки: {e}")
        await message.answer(
            "❌ Помилка активації підписки. Зверніться до підтримки.\n"
            f"ID транзакції: {payment.telegram_payment_charge_id}"
        )

async def handle_subscription_info(callback_query: types.CallbackQuery):
    """Показує детальну інформацію про підписку"""
    try:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_profile")
        )
        
        info_text = (
            "💫 <b>Підписка на AI аналіз угод</b>\n\n"
            "📊 <b>Що включено:</b>\n"
            "• Необмежений аналіз торгових графіків\n"
            "• Технічний аналіз з рекомендаціями\n"
            "• Рівні входу, стоп-лосс та тейк-профіт\n"
            "• Рекомендації по плечу\n"
            "• Детальне обґрунтування кожної угоди\n\n"
            "💰 <b>Вартість:</b> 250 Telegram Stars\n"
            "⏰ <b>Термін дії:</b> 30 днів\n\n"
            "🔄 <b>Поновлення:</b> Автоматично не поновлюється\n"
            "💳 <b>Оплата:</b> Через Telegram Stars"
        )
        
        try:
            await callback_query.message.edit_text(
                info_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception:
            # Якщо не можемо редагувати, надсилаємо нове повідомлення
            await callback_query.message.answer(
                info_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
        await callback_query.answer()
        
    except Exception as e:
        logging.error(f"Помилка показу інформації про підписку: {e}")
        await callback_query.answer("❌ Помилка завантаження інформації", show_alert=True)

async def handle_back_to_profile(callback_query: types.CallbackQuery):
    """Повертає назад до профілю"""
    await show_profile(callback_query)

def register_payment_handlers(dp):
    """Реєструє всі обробники платежів"""
    dp.register_callback_query_handler(handle_subscribe, text="subscribe_30_days")
    dp.register_callback_query_handler(handle_subscription_info, text="subscription_info")
    dp.register_callback_query_handler(handle_back_to_profile, text="back_to_profile")
    dp.register_pre_checkout_query_handler(handle_pre_checkout_query)
    dp.register_message_handler(handle_successful_payment, content_types=types.ContentType.SUCCESSFUL_PAYMENT) 