# Crypto Future Trading Bot

AI-асистент для аналізу ф'ючерсних угод з криптовалютами в Telegram.

## Функціональність

- 🤖 AI-аналіз торгових графіків
- 📊 Технічний аналіз з рекомендаціями
- 💰 Система підписки через Telegram Stars
- 👤 Профіль користувача з статистикою
- 🎯 Рівні входу, стоп-лосс та тейк-профіт
- ⚖️ Рекомендації по плечу

## Розгортання на сервері

### Підготовка

1. **Клонуйте репозиторій:**
```bash
git clone <your-repo-url>
cd cryptoFuture
```

2. **Створіть .env файл:**
```bash
cp env.example .env
```

3. **Заповніть .env файл:**
```env
BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
ADMIN_ID=your_telegram_id_here
DB_DSN=postgresql://patrick:Getting Started@postgres:5432/casino
```

### Запуск з Docker

1. **Збудуйте та запустіть контейнери:**
```bash
docker-compose up -d
```

2. **Перевірте статус:**
```bash
docker-compose ps
```

3. **Перегляньте логи:**
```bash
docker-compose logs -f bot
```

### Команди управління

- **Зупинити бота:**
```bash
docker-compose stop
```

- **Перезапустити бота:**
```bash
docker-compose restart bot
```

- **Оновити код:**
```bash
git pull
docker-compose build bot
docker-compose up -d bot
```

- **Резервне копіювання БД:**
```bash
docker-compose exec postgres pg_dump -U patrick casino > backup.sql
```

### Моніторинг

- **Логи бота:** `docker-compose logs -f bot`
- **Логи БД:** `docker-compose logs -f postgres`
- **Статус контейнерів:** `docker-compose ps`

## Налаштування

### Отримання токенів

1. **Telegram Bot Token:**
   - Напишіть @BotFather в Telegram
   - Створіть нового бота командою `/newbot`
   - Скопіюйте токен

2. **OpenAI API Key:**
   - Зареєструйтесь на https://platform.openai.com/
   - Створіть API ключ в розділі API Keys

3. **Admin ID:**
   - Напишіть @userinfobot в Telegram
   - Отримайте свій ID

### Налаштування Telegram Stars

1. Увійдіть в @BotFather
2. Оберіть свого бота
3. Перейдіть в Bot Settings → Payments
4. Підключіть Telegram Stars як провайдера платежів

## Структура проекту

```
cryptoFuture/
├── bot/
│   ├── handlers/          # Обробники команд
│   ├── keyboards/         # Клавіатури
│   └── ai.py             # AI аналіз
├── db/
│   └── queries.py        # Запити до БД
├── config.py             # Конфігурація
├── main.py               # Точка входу
├── Dockerfile            # Docker образ
├── docker-compose.yml    # Docker Compose
├── requirements.txt      # Python залежності
└── init.sql             # Ініціалізація БД
```

## Підтримка

Якщо виникли проблеми:

1. Перевірте логи: `docker-compose logs -f bot`
2. Перевірте статус БД: `docker-compose exec postgres pg_isready`
3. Перезапустіть сервіси: `docker-compose restart`

## Безпека

- Ніколи не публікуйте .env файл
- Регулярно оновлюйте залежності
- Використовуйте HTTPS для webhook (якщо потрібно)
- Обмежте доступ до сервера 