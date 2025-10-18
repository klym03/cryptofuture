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

# =============== АДМІНІСТРАТИВНІ КЛАВІАТУРИ ===============

# Головна адмін панель
admin_main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Управління користувачами", callback_data="admin_users"),
            InlineKeyboardButton(text="🔗 Реферальні посилання", callback_data="admin_referrals")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="⚙️ Налаштування", callback_data="admin_settings")
        ]
    ]
)

# Управління користувачами
admin_users_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Надати підписку", callback_data="admin_grant_subscription"),
            InlineKeyboardButton(text="🎁 Надати спроби", callback_data="admin_grant_tries")
        ],
        [
            InlineKeyboardButton(text="🔍 Пошук користувача", callback_data="admin_search_user")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад до головної", callback_data="admin_main")
        ]
    ]
)

# Реферальні посилання
admin_referrals_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Створити посилання", callback_data="admin_create_referral"),
            InlineKeyboardButton(text="📋 Список посилань", callback_data="admin_list_referrals")
        ],
        [
            InlineKeyboardButton(text="📈 Статистика посилань", callback_data="admin_referral_stats")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад до головної", callback_data="admin_main")
        ]
    ]
)

# Навігація по реферальних посиланнях
def admin_referral_navigation_keyboard(links, page=0, per_page=5) -> InlineKeyboardMarkup:
    keyboard = []
    
    # Додаємо кнопки для кожного посилання на поточній сторінці
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(links))
    
    for i in range(start_idx, end_idx):
        link = links[i]
        status_emoji = "🟢" if link['is_active'] else "🔴"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {link['name']} ({link['registrations']}👥/{link['subscriptions']}💎)",
                callback_data=f"admin_referral_detail_{link['code']}"
            )
        ])
    
    # Кнопки навігації
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Попередня", callback_data=f"admin_referrals_page_{page-1}"))
    if end_idx < len(links):
        nav_buttons.append(InlineKeyboardButton(text="Наступна ➡️", callback_data=f"admin_referrals_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_referrals")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Детальна інформація про реферальне посилання
def admin_referral_detail_keyboard(code: str, is_active: bool) -> InlineKeyboardMarkup:
    status_text = "🔴 Деактивувати" if is_active else "🟢 Активувати"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=status_text, callback_data=f"admin_toggle_referral_{code}"),
                InlineKeyboardButton(text="📋 Копіювати посилання", callback_data=f"admin_copy_referral_{code}")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад до списку", callback_data="admin_list_referrals")
            ]
        ]
    ) 