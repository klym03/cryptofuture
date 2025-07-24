# Використовуємо офіційний Python образ
FROM python:3.9-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо файл з залежностями
COPY requirements.txt .

# Оновлюємо pip та встановлюємо Python залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код додатка
COPY . .

# Створюємо непривілейованого користувача
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Відкриваємо порт (якщо потрібно)
EXPOSE 8000

# Команда для запуску бота
CMD ["python", "main.py"] 