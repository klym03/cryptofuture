import base64
import io
import logging
import os
from aiogram import Dispatcher, types
from db import queries as db
from bot.ai import get_trade_recommendation
from bot.keyboards.reply import subscribe_keyboard
from datetime import datetime, timezone


async def handle_photo(message: types.Message):
    """
    Хендлер для обробки надісланих фотографій.
    """
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user:
        await message.answer("Будь ласка, почніть з команди /start, щоб я міг вас зареєструвати.")
        return

    # Перевіряємо, чи не закінчився термін підписки
    subscription_expires_at = user["subscription_expires_at"]
    if subscription_expires_at and subscription_expires_at.tzinfo is None:
        subscription_expires_at = subscription_expires_at.replace(tzinfo=timezone.utc)

    if user["is_subscribed"] and subscription_expires_at < datetime.now(timezone.utc):
        # Тут можна було б оновити статус, але для простоти просто повідомимо
        await message.answer(
            "Термін вашої підписки закінчився. Будь ласка, поновіть її, щоб продовжити користуватися ботом.",
            reply_markup=subscribe_keyboard
        )
        return

    # Основна логіка перевірки доступу
    if not user["is_subscribed"] and user["free_trades_left"] <= 0:
        await message.answer(
            "На жаль, ваші безкоштовні спроби закінчилися. "
            "Щоб продовжити, будь ласка, оформіть підписку.",
            reply_markup=subscribe_keyboard
        )
        return

    processing_message = await message.answer("🔄 Аналізую ваш графік... Це може зайняти до хвилини.")

    try:
        # Отримуємо файл фотографії
        photo = message.photo[-1]  # Беремо найбільший розмір
        file_info = await message.bot.get_file(photo.file_id)
        
        # Завантажуємо фото в пам'ять
        photo_bytes = io.BytesIO()
        await message.bot.download_file(file_info.file_path, photo_bytes)
        photo_bytes.seek(0)
        
        # Кодуємо в base64
        base64_image = base64.b64encode(photo_bytes.read()).decode('utf-8')
        mime_type = "image/jpeg"

        # Отримуємо аналіз від AI
        analysis_text = await get_trade_recommendation(base64_image, mime_type)
        
        # Додаємо рекомендацію про управління капіталом
        capital_management = (
            "\n\n"
            "💰 <b>Управління капіталом:</b>\n"
            "Рекомендується заходити в угоду з <b>не більше 10% від загального банку</b>. "
            "Це дозволить вам залишатися в грі навіть при серії невдалих угод і убезпечить ваш депозит від значних втрат."
        )
        analysis_text += capital_management

        # Списуємо безкоштовну спробу, якщо це не підписник
        if not user["is_subscribed"]:
            await db.use_free_trade(user_id)
            
        # Відправляємо результат з обробкою HTML помилок
        try:
            await message.answer(analysis_text, parse_mode="HTML")
        except Exception as html_error:
            # Якщо HTML невалідний, спробуємо видалити всі HTML теги і відправити
            logging.error(f"Помилка HTML форматування: {html_error}")
            try:
                from bot.ai import remove_all_html_tags
                clean_text = remove_all_html_tags(analysis_text)
                await message.answer(
                    "🔄 <b>Результат аналізу</b> (форматування спрощено через технічні обмеження):\n\n" + clean_text,
                    parse_mode="HTML"
                )
            except Exception:
                # Якщо й це не працює, відправляємо зовсім без форматування
                await message.answer(
                    "Результат аналізу (без форматування):\n\n" + analysis_text
                )

    except Exception as e:
        logging.error(f"Помилка під час аналізу угоди для користувача {user['user_id']}: {e}")
        await message.answer("На жаль, сталася помилка під час обробки вашого запиту. Спробуйте ще раз пізніше.")
    finally:
        await processing_message.delete()


def register_trade_handlers(dp: Dispatcher):
    """Реєструє хендлери для обробки торгових запитів."""
    dp.register_message_handler(handle_photo, content_types=["photo"]) 