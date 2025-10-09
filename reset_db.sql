-- Скрипт для повного перестворення бази даних з правильною схемою

-- Видаляємо старі таблиці якщо вони існують
DROP TABLE IF EXISTS referral_stats CASCADE;
DROP TABLE IF EXISTS referral_links CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Створюємо таблицю користувачів з усіма необхідними колонками
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    free_trades_left INT DEFAULT 1,
    is_subscribed BOOLEAN DEFAULT FALSE,
    subscription_expires_at TIMESTAMP,
    referral_code TEXT, -- реферальний код через який прийшов користувач
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Створюємо таблицю реферальних посилань
CREATE TABLE referral_links (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL, -- назва/опис силки
    admin_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Створюємо таблицю статистики реферальних посилань
CREATE TABLE referral_stats (
    id SERIAL PRIMARY KEY,
    referral_code TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    action_type TEXT NOT NULL, -- 'click', 'register', 'subscription'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referral_code) REFERENCES referral_links(code) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Створюємо індекси для оптимізації
CREATE INDEX idx_users_subscription ON users(is_subscribed, subscription_expires_at);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_referral_links_code ON referral_links(code);
CREATE INDEX idx_referral_links_admin ON referral_links(admin_id);
CREATE INDEX idx_referral_stats_code ON referral_stats(referral_code);
CREATE INDEX idx_referral_stats_action ON referral_stats(action_type);

-- Інформаційне повідомлення
SELECT 'База даних успішно перестворена з новою схемою!' as result;
