import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_DSN = os.getenv("DB_DSN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")

# --- Перевірка наявності всіх необхідних змінних ---
if not BOT_TOKEN:
    sys.exit("🔴 Помилка: BOT_TOKEN не знайдено. Будь ласка, додайте токен вашого бота у файл .env")

if not OPENAI_API_KEY:
    sys.exit("🔴 Помилка: OPENAI_API_KEY не знайдено. Будь ласка, додайте ваш ключ OpenAI API у файл .env")
    
if not DB_DSN:
    sys.exit(
        "🔴 Помилка: DB_DSN не знайдено. Будь ласка, додайте рядок підключення до вашої бази даних у файл .env.\n"
        "   Приклад для вашого випадку: DB_DSN=postgresql://admin@localhost:5432/casino"
    )

if not ADMIN_ID:
    print("⚠️ Попередження: ADMIN_ID не встановлено у файлі .env. Адміністративні команди не будуть працювати.")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}" 