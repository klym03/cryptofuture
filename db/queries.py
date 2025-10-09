import asyncpg
import logging
import random
import string
from datetime import datetime, timedelta
from config import DB_DSN

pool: asyncpg.Pool = None

async def create_pool():
    global pool
    try:
        pool = await asyncpg.create_pool(dsn=DB_DSN)
        logging.info("Створено пул підключень до бази даних.")
    except Exception as e:
        logging.error(f"Помилка створення пулу підключень: {e}")
        raise

async def close_pool():
    global pool
    if pool:
        await pool.close()
        logging.info("Пул підключень до бази даних закрито.")

async def create_tables():
    async with pool.acquire() as conn:
        # Створення таблиці користувачів з усіма колонками
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                free_trades_left INT DEFAULT 1,
                is_subscribed BOOLEAN DEFAULT FALSE,
                subscription_expires_at TIMESTAMP,
                referral_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        # Додаємо колонку referral_code якщо її немає (для існуючих БД)
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
        except Exception:
            pass  # Колонка вже існує
        
        # Додаємо колонку created_at якщо її немає (для існуючих БД)
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass  # Колонка вже існує
        
        # Створення таблиці реферальних посилань
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS referral_links (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                admin_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """
        )
        
        # Створення таблиці статистики реферальних посилань
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS referral_stats (
                id SERIAL PRIMARY KEY,
                referral_code TEXT NOT NULL,
                user_id BIGINT NOT NULL,
                action_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        # Створення індексів для оптимізації
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(is_subscribed, subscription_expires_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_referral_links_code ON referral_links(code)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_referral_links_admin ON referral_links(admin_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_referral_stats_code ON referral_stats(referral_code)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_referral_stats_action ON referral_stats(action_type)")
        
        logging.info("Всі таблиці та індекси успішно створені/оновлені")

async def get_user(user_id: int):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(user) if user else None

async def add_user(user_id: int, username: str, first_name: str, referral_code: str = None):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, referral_code) 
            VALUES ($1, $2, $3, $4) 
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
            username,
            first_name,
            referral_code,
        )

async def use_free_trade(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET free_trades_left = free_trades_left - 1 WHERE user_id = $1 AND free_trades_left > 0",
            user_id
        )

async def activate_subscription(user_id: int):
    async with pool.acquire() as conn:
        expires_at = datetime.now() + timedelta(days=30)
        await conn.execute(
            """
            UPDATE users 
            SET is_subscribed = TRUE, subscription_expires_at = $1
            WHERE user_id = $2
            """,
            expires_at,
            user_id,
        )

async def update_subscription_status(user_id: int, is_subscribed: bool):
    """Оновлює статус підписки користувача"""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users 
            SET is_subscribed = $1
            WHERE user_id = $2
            """,
            is_subscribed,
            user_id,
        )

# =============== РЕФЕРАЛЬНА СИСТЕМА ===============

def generate_referral_code(length: int = 8) -> str:
    """Генерує випадковий реферальний код"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def create_referral_link(admin_id: int, name: str) -> str:
    """Створює новий реферальний код"""
    async with pool.acquire() as conn:
        while True:
            code = generate_referral_code()
            try:
                await conn.execute(
                    """
                    INSERT INTO referral_links (code, name, admin_id)
                    VALUES ($1, $2, $3)
                    """,
                    code, name, admin_id
                )
                return code
            except asyncpg.UniqueViolationError:
                # Якщо код вже існує, генеруємо новий
                continue

async def get_referral_link(code: str):
    """Отримує інформацію про реферальний код"""
    async with pool.acquire() as conn:
        link = await conn.fetchrow(
            "SELECT * FROM referral_links WHERE code = $1 AND is_active = TRUE",
            code
        )
        return dict(link) if link else None

async def get_admin_referral_links(admin_id: int):
    """Отримує всі реферальні посилання адміна"""
    async with pool.acquire() as conn:
        links = await conn.fetch(
            """
            SELECT rl.*, 
                   COUNT(CASE WHEN rs.action_type = 'register' THEN 1 END) as registrations,
                   COUNT(CASE WHEN rs.action_type = 'subscription' THEN 1 END) as subscriptions
            FROM referral_links rl
            LEFT JOIN referral_stats rs ON rl.code = rs.referral_code
            WHERE rl.admin_id = $1
            GROUP BY rl.id, rl.code, rl.name, rl.admin_id, rl.created_at, rl.is_active
            ORDER BY rl.created_at DESC
            """,
            admin_id
        )
        return [dict(link) for link in links]

async def toggle_referral_link_status(code: str, admin_id: int):
    """Змінює статус активності реферального посилання"""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE referral_links 
            SET is_active = NOT is_active 
            WHERE code = $1 AND admin_id = $2
            """,
            code, admin_id
        )

async def add_referral_stat(referral_code: str, user_id: int, action_type: str):
    """Додає статистику використання реферального коду"""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO referral_stats (referral_code, user_id, action_type)
            VALUES ($1, $2, $3)
            """,
            referral_code, user_id, action_type
        )

async def get_referral_stats_summary(admin_id: int):
    """Отримує загальну статистику реферальних посилань адміна"""
    async with pool.acquire() as conn:
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(DISTINCT rl.code) as total_links,
                COUNT(CASE WHEN rs.action_type = 'register' THEN 1 END) as total_registrations,
                COUNT(CASE WHEN rs.action_type = 'subscription' THEN 1 END) as total_subscriptions
            FROM referral_links rl
            LEFT JOIN referral_stats rs ON rl.code = rs.referral_code
            WHERE rl.admin_id = $1
            """,
            admin_id
        )
        return dict(stats) if stats else {"total_links": 0, "total_registrations": 0, "total_subscriptions": 0}

# =============== АДМІН ФУНКЦІЇ ===============

async def admin_grant_subscription(user_id: int):
    """Адмін надає підписку користувачу"""
    async with pool.acquire() as conn:
        expires_at = datetime.now() + timedelta(days=30)
        await conn.execute(
            """
            UPDATE users 
            SET is_subscribed = TRUE, subscription_expires_at = $1
            WHERE user_id = $2
            """,
            expires_at, user_id
        )

async def admin_grant_free_tries(user_id: int, count: int = 1):
    """Адмін надає безкоштовні спроби користувачу"""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users 
            SET free_trades_left = free_trades_left + $1
            WHERE user_id = $2
            """,
            count, user_id
        )

async def get_user_by_username(username: str):
    """Знаходить користувача за username"""
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            username
        )
        return dict(user) if user else None

async def search_users(query: str, limit: int = 10):
    """Пошук користувачів за username або first_name"""
    async with pool.acquire() as conn:
        users = await conn.fetch(
            """
            SELECT user_id, username, first_name, is_subscribed, free_trades_left
            FROM users 
            WHERE username ILIKE $1 OR first_name ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            f"%{query}%", limit
        )
        return [dict(user) for user in users]

# =============== ЗАГАЛЬНА СТАТИСТИКА БОТА ===============

async def get_bot_stats():
    """Отримує загальну статистику бота"""
    async with pool.acquire() as conn:
        # Загальна кількість користувачів
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        # Активні підписки
        active_subscriptions = await conn.fetchval(
            """
            SELECT COUNT(*) FROM users 
            WHERE is_subscribed = TRUE 
            AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
            """
        )
        
        # Користувачі за останні 7 днів
        recent_users = await conn.fetchval(
            """
            SELECT COUNT(*) FROM users 
            WHERE created_at > NOW() - INTERVAL '7 days'
            """
        )
        
        # Загальна кількість реферальних посилань
        total_referral_links = await conn.fetchval("SELECT COUNT(*) FROM referral_links")
        
        # Загальна кількість переходів по реферальних посиланнях
        total_referral_clicks = await conn.fetchval(
            "SELECT COUNT(*) FROM referral_stats WHERE action_type = 'register'"
        )
        
        # Загальна кількість підписок через реферальні посилання
        referral_subscriptions = await conn.fetchval(
            "SELECT COUNT(*) FROM referral_stats WHERE action_type = 'subscription'"
        )
        
        return {
            "total_users": total_users or 0,
            "active_subscriptions": active_subscriptions or 0,
            "recent_users": recent_users or 0,
            "total_referral_links": total_referral_links or 0,
            "total_referral_clicks": total_referral_clicks or 0,
            "referral_subscriptions": referral_subscriptions or 0
        } 