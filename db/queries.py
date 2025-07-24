import asyncpg
import logging
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
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                free_trades_left INT DEFAULT 1,
                is_subscribed BOOLEAN DEFAULT FALSE,
                subscription_expires_at TIMESTAMP
            )
            """
        )

async def get_user(user_id: int):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(user) if user else None

async def add_user(user_id: int, username: str, first_name: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, first_name) 
            VALUES ($1, $2, $3) 
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
            username,
            first_name,
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