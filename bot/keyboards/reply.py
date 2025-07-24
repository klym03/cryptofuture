from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👤 Профіль"),
            KeyboardButton(text="💡 Допомога з угодою"),
        ],
    ],
    resize_keyboard=True
)

subscribe_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Оформити підписку (30 днів)", callback_data="subscribe_30_days")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Детальніше про підписку", callback_data="subscription_info")
        ]
    ]
)

# Клавіатура для детальної інформації про підписку
subscription_info_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Оформити підписку (30 днів)", callback_data="subscribe_30_days")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_subscription")
        ]
    ]
) 