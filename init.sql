-- Створення таблиці користувачів
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    free_trades_left INT DEFAULT 1,
    is_subscribed BOOLEAN DEFAULT FALSE,
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Створення індексів для оптимізації
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(is_subscribed, subscription_expires_at);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Додаткові налаштування
ALTER DATABASE casino SET timezone TO 'UTC'; 