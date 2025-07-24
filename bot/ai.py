import openai
from config import OPENAI_API_KEY
import logging
import re

# Ініціалізуємо асинхронний клієнт OpenAI
client = None

def get_openai_client():
    global client
    if client is None:
        try:
            client = openai.AsyncOpenAI(
                api_key=OPENAI_API_KEY,
                timeout=60.0
            )
        except Exception as e:
            logging.error(f"Помилка ініціалізації OpenAI клієнта: {e}")
            raise
    return client

def fix_html_tags(content: str) -> str:
    """
    Виправляє незакриті та неправильні HTML теги в контенті
    """
    if not content:
        return content
    
    # Спочатку виправляємо неправильні теги типу </b</b> -> </b>
    content = re.sub(r'</(\w+)</\1>', r'</\1>', content)
    
    # Виправляємо подвійні теги типу </b></b> -> </b>
    content = re.sub(r'</(\w+)></\1>', r'</\1>', content)
    
    # Виправляємо неправильні закриваючі теги типу </b</b> -> </b>
    content = re.sub(r'</(\w+)</', r'</\1>', content)
    
    # Рахуємо відкриті та закриті теги
    open_tags = {}
    
    # Знаходимо всі правильні теги
    tag_pattern = r'<(/?)(\w+)(?:\s[^>]*)?>'
    matches = list(re.finditer(tag_pattern, content))
    
    for match in matches:
        is_closing, tag_name = match.groups()
        
        if is_closing:
            # Закриваючий тег
            if tag_name in open_tags and open_tags[tag_name] > 0:
                open_tags[tag_name] -= 1
        else:
            # Відкриваючий тег
            open_tags[tag_name] = open_tags.get(tag_name, 0) + 1
    
    # Додаємо закриваючі теги для незакритих
    for tag_name, count in open_tags.items():
        if count > 0:
            content += f'</{tag_name}>' * count
            logging.warning(f"Додано {count} закриваючих тегів для <{tag_name}>")
    
    # Видаляємо неправильні теги, які не вдалося виправити
    content = re.sub(r'<[^>]*<[^>]*>', '', content)
    
    return content

SYSTEM_PROMPT = """
Ти — експерт з технічного аналізу криптовалютних графіків. Твоє завдання — виключно аналізувати візуальну інформацію з наданого зображення графіка. Ти не даєш фінансових порад. Твоя мета — ідентифікувати технічні патерни, рівні та потенційні сценарії руху ціни.

Твоя відповідь ПОВИННА бути відформатована за допомогою HTML-тегів для Telegram. Використовуй <b> для жирного тексту та <code> для всіх тикерів та числових значень.

ВАЖЛИВО: Кожен відкритий HTML тег ОБОВ'ЯЗКОВО має бути закритий. Наприклад: <b>текст</b>, <code>значення</code>. Не залишай незакриті теги!
ЗАБОРОНЕНО: Не використовуй подвійні або неправильні теги типу </b</b> або </b></b>. Використовуй тільки правильні теги!

Ось структура, якої ти маєш СУВОРО дотримуватися:

📊 <b>Технічний аналіз графіка</b>

<b>Інструмент:</b> <code>[Назва монети, якщо видно на графіку]</code>
<b>Потенційний напрямок:</b> <code>[Ймовірний рух Long/Short]</code> [Додай емодзі 🟢 для Long або 🔴 для Short]

▫️ <b>Ключові рівні для входу:</b> <code>[Ціновий діапазон]</code>
▫️ <b>Рівень для обмеження ризику (Stop-Loss):</b> <code>[Ціна]</code>
▫️ <b>Рекомендоване плече:</b> <code>[Наприклад: 3x-5x]</code>

▫️ <b>Потенційні цілі (Take Profit):</b>
  1. <code>[Перша ціль]</code>
  2. <code>[Друга ціль]</code>

<blockquote expandable><b>📈 Аналітичне обґрунтування:</b>
[Тут детальний, але лаконічний технічний аналіз. Опиши, що ти бачиш на графіку: патерни, індикатори, рівні підтримки/опору. Поясни, чому ти припускаєш такий сценарій руху та чому рекомендуєш саме таке плече.]</blockquote>

<blockquote expandable><b>⚠️ Відмова від відповідальності:</b>
Ця інформація є виключно результатом технічного аналізу візуальних даних і не є фінансовою порадою чи торговою рекомендацією. Всі рішення приймаються на ваш власний ризик.</blockquote>

<blockquote expandable><b>⚖️ Важливо про плече:</b>
Рекомендоване плече базується на технічному аналізі волатільності та ризику угоди. Високе плече збільшує як потенційний прибуток, так і ризик втрат. Завжди використовуйте Stop-Loss та управляйте ризиками.</blockquote>
"""

async def get_trade_recommendation(base64_image: str, mime_type: str = "image/jpeg") -> str:
    """
    Аналізує зображення торгового графіка за допомогою OpenAI GPT-4o та повертає рекомендацію.
    """
    try:
        client_instance = get_openai_client()
        response = await client_instance.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Проведи технічний аналіз зображення графіка нижче. Ідентифікуй патерни, ключові рівні та потенційний сценарій руху ціни. Сформуй відповідь згідно з наданою структурою в системних інструкціях."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        content = response.choices[0].message.content
        
        # Якщо OpenAI відмовляється аналізувати
        if content and ("I'm sorry" in content or "can't help" in content or "I cannot" in content):
            return """⚠️ <b>Система не може проаналізувати це зображення</b>

Можливі причини:
▫️ Зображення не містить чіткий графік
▫️ Низька якість або розмір зображення
▫️ Неприйнятний контент для аналізу

💡 <b>Рекомендації:</b>
▫️ Надішліть скріншот графіка з TradingView
▫️ Переконайтесь, що графік чіткий і читабельний
▫️ Уникайте зображень з особистою інформацією

Спробуйте надіслати інше зображення графіка."""
        
        # Валідація та виправлення HTML тегів
        if content:
            logging.info(f"Отримано відповідь від OpenAI: {content[:200]}...")
            original_content = content
            content = fix_html_tags(content)
            if original_content != content:
                logging.warning(f"HTML теги були виправлені. Оригінал: {original_content[-100:]}")
                logging.warning(f"Після виправлення: {content[-100:]}")
            logging.info("HTML теги валідовано та виправлено")
        
        return content
    except Exception as e:
        logging.error(f"Помилка виклику OpenAI API: {e}")
        # Якщо відповідь містить відмову, повертаємо більш детальну інформацію
        if "I'm sorry" in str(e) or "can't help" in str(e):
            return "⚠️ OpenAI відмовився аналізувати зображення. Можливо, зображення не містить торговий графік або має неприйнятний контент. Спробуйте надіслати інше зображення графіка."
        # Якщо помилка HTML парсингу
        if "can't parse entities" in str(e) or "can't find end tag" in str(e):
            return "⚠️ Помилка форматування відповіді. Спробуйте надіслати зображення ще раз."
        return "На жаль, під час аналізу зображення сталася помилка. Спробуйте, будь ласка, пізніше." 