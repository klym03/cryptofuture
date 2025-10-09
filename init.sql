-- Створення таблиці користувачів
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    free_trades_left INT DEFAULT 1,
    is_subscribed BOOLEAN DEFAULT FALSE,
    subscription_expires_at TIMESTAMP,
    referral_code TEXT, -- реферальний код через який прийшов користувач
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Створення таблиці реферальних посилань
CREATE TABLE IF NOT EXISTS referral_links (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL, -- назва/опис силки
    admin_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Створення таблиці статистики реферальних посилань
CREATE TABLE IF NOT EXISTS referral_stats (
    id SERIAL PRIMARY KEY,
    referral_code TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    action_type TEXT NOT NULL, -- 'click', 'register', 'subscription'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referral_code) REFERENCES referral_links(code) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Створення індексів для оптимізації
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(is_subscribed, subscription_expires_at);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_referral_links_code ON referral_links(code);
CREATE INDEX IF NOT EXISTS idx_referral_links_admin ON referral_links(admin_id);
CREATE INDEX IF NOT EXISTS idx_referral_stats_code ON referral_stats(referral_code);
CREATE INDEX IF NOT EXISTS idx_referral_stats_action ON referral_stats(action_type);

-- Додаткові налаштування
ALTER DATABASE casino SET timezone TO 'UTC'; 