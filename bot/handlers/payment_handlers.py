from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import queries as db
import logging
from bot.handlers.user_handlers import show_profile

async def handle_subscribe(callback_query: types.CallbackQuery):
    """Обробляє натискання кнопки підписки - направляє до адміністратора"""
    try:
        await callback_query.message.edit_text(
            "💎 <b>Оформлення підписки</b>\n\n"
            "Для оформлення підписки на AI аналіз торгових угод "
            "зверніться до нашого адміністратора:\n\n"
            "👤 <b>Контакт:</b> @kicenyk\n\n"
            "📝 <b>Що включено в підписку:</b>\n"
            "• Необмежений аналіз торгових графіків\n"
            "• Технічний аналіз з рекомендаціями\n"
            "• Рівні входу, стоп-лосс та тейк-профіт\n"
            "• Рекомендації по плечу\n"
            "• Детальне обґрунтування кожної угоди\n\n"
            "⏰ <b>Термін дії:</b> 30 днів\n\n"
            "Напишіть @kicenyk для оформлення підписки!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✉️ Написати @kicenyk", 
                            url="https://t.me/kicenyk"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад до профілю", 
                            callback_data="back_to_profile"
                        )
                    ]
                ]
            ),
            parse_mode="HTML"
        )
        await callback_query.answer()
        
    except Exception as e:
        logging.error(f"Помилка показу інформації про підписку: {e}")
        await callback_query.answer("❌ Помилка завантаження інформації", show_alert=True)

async def handle_subscription_info(callback_query: types.CallbackQuery):
    """Показує детальну інформацію про підписку"""
    try:
        await callback_query.message.edit_text(
            "💫 <b>Підписка на AI аналіз угод</b>\n\n"
            "📊 <b>Що включено:</b>\n"
            "• Необмежений аналіз торгових графіків\n"
            "• Технічний аналіз з рекомендаціями\n"
            "• Рівні входу, стоп-лосс та тейк-профіт\n"
            "• Рекомендації по плечу\n"
            "• Детальне обґрунтування кожної угоди\n\n"
            "⏰ <b>Термін дії:</b> 30 днів\n"
            "🔄 <b>Поновлення:</b> Через адміністратора\n\n"
            "💬 <b>Для оформлення:</b>\n"
            "Зверніться до @kicenyk для отримання підписки",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✉️ Написати @kicenyk", 
                            url="https://t.me/kicenyk"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад до профілю", 
                            callback_data="back_to_profile"
                        )
                    ]
                ]
            ),
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