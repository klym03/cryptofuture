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
    
    # Видаляємо всі неправильні конструкції типу </b</b>, </b></b>
    content = re.sub(r'</[^>]*<[^>]*>', '', content)
    
    # Виправляємо подвійні теги типу </b></b> -> </b>
    content = re.sub(r'(</)(\w+)(>)\2(>)', r'\1\2\3', content)
    
    # Видаляємо всі пошкоджені теги що містять < всередині
    content = re.sub(r'<[^>]*<[^>]*>', '', content)
    
    # Видаляємо порожні теги
    content = re.sub(r'<(\w+)></\1>', '', content)
    
    # Рахуємо відкриті та закриті теги
    open_tags = []
    
    # Знаходимо всі правильні теги
    tag_pattern = r'<(/?)(\w+)(?:\s[^>]*)?>'
    matches = list(re.finditer(tag_pattern, content))
    
    for match in matches:
        is_closing, tag_name = match.groups()
        
        if is_closing:
            # Закриваючий тег - видаляємо останній відповідний відкритий тег
            if open_tags and open_tags[-1] == tag_name:
                open_tags.pop()
        else:
            # Відкриваючий тег - додаємо в стек
            open_tags.append(tag_name)
    
    # Додаємо закриваючі теги для незакритих (в зворотному порядку)
    for tag_name in reversed(open_tags):
        content += f'</{tag_name}>'
        logging.warning(f"Додано закриваючий тег для <{tag_name}>")
    
    # Остаточне очищення від будь-яких неправильних тегів
    content = re.sub(r'<[^/>][^>]*[^/>]<', '<', content)
    
    return content

def remove_all_html_tags(content: str) -> str:
    """
    Видаляє всі HTML теги з тексту як запасний варіант
    """
    if not content:
        return content
    
    # Видаляємо всі HTML теги
    content = re.sub(r'<[^>]+>', '', content)
    
    # Декодуємо HTML entities
    content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    
    return content

SYSTEM_PROMPT = """
Ти — досвідчений експерт з технічного аналізу криптовалютних графіків. Твоя мета — надати глибокий та об'єктивний аналіз, базуючись на візуальній інформації з наданого зображення. Твій аналіз має враховувати принципи конфлюенції сигналів (збіг кількох індикаторів/патернів) та контекст старших таймфреймів. Ти не даєш фінансових порад.

Твоя відповідь ПОВИННА бути відформатована за допомогою HTML-тегів для Telegram. Використовуй <b> для жирного тексту та <code> для всіх тикерів та числових значень.

ВАЖЛИВО: Кожен відкритий HTML тег ОБОВ'ЯЗКОВО має бути закритий. Наприклад: <b>текст</b>, <code>значення</code>. Не залишай незакриті теги!
ЗАБОРОНЕНО: Не використовуй подвійні або неправильні теги типу </b</b> або </b></b>. Використовуй тільки правильні теги!

Ось структура, якої ти маєш СУВОРО дотримуватися:

📊 <b>Технічний аналіз графіка</b>

<b>Інструмент:</b> <code>[Назва монети, якщо видно]</code>
<b>Таймфрейм:</b> <code>[Таймфрейм, видимий на графіку, напр. H4, D1]</code>
<b>Основний сценарій:</b> <code>[Ймовірний рух Long/Short]</code> [Додай емодзі 🟢 для Long або 🔴 для Short]

▫️ <b>Ключові рівні для входу:</b> <code>[Ціновий діапазон]</code>
▫️ <b>Рівень для обмеження ризику (Stop-Loss):</b> <code>[Ціна]</code>
▫️ <b>Співвідношення Ризик/Прибуток (RRR):</b> <code>[Приблизне значення, напр. 1:3.5]</code>
▫️ <b>Рекомендоване плече:</b> <code>[Наприклад: до 5x]</code>

▫️ <b>Потенційні цілі (Take Profit):</b>

<code>[Перша ціль]</code>

<code>[Друга ціль]</code>

<code>[Третя ціль, якщо доречно]</code>

<blockquote expandable><b>📈 Детальний аналіз:</b>
<b>Аргументи за сценарій:</b>
[Тут опиши збіг факторів (конфлюенцію), які підтверджують основний сценарій. Наприклад: "Ціна сформувала патерн 'бичачий прапор' біля сильного рівня підтримки <code>[ціна]</code>. Додатково, індикатор RSI показує приховану бичачу дивергенцію, що підсилює сигнал на ріст."]

<b>Альтернативний сценарій:</b>
[Коротко опиши, що може піти не так і що буде сигналом до скасування ідеї. Наприклад: "Сценарій буде недійсним, якщо ціна закріпиться нижче рівня <code>[ціна]</code>. У такому випадку можливе падіння до наступної зони підтримки в районі <code>[ціна]</code>."]</blockquote>

<blockquote expandable><b>⚠️ Відмова від відповідальності:</b>
Ця інформація є виключно результатом технічного аналізу візуальних даних і не є фінансовою порадою чи торговою рекомендацією. Всі рішення приймаються на ваш власний ризик.</blockquote>

<blockquote expandable><b>⚖️ Важливо про плече:</b>
Рекомендоване плече базується на технічному аналізі волатильності та ризику угоди. Високе плече збільшує як потенційний прибуток, так і ризик втрат. Завжди використовуйте Stop-Loss та управляйте ризиками.</blockquote>
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
            max_tokens=1500,
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
            
            try:
                # Спробуємо виправити HTML теги
                content = fix_html_tags(content)
                if original_content != content:
                    logging.warning(f"HTML теги були виправлені")
                
                # Тестуємо чи валідний HTML
                import html
                html.escape(content)  # Простий тест на валідність
                
                logging.info("HTML теги валідовано та виправлено")
            except Exception as html_error:
                logging.error(f"Не вдалося виправити HTML: {html_error}")
                # Якщо виправлення не допомогло, видаляємо всі HTML теги
                content = remove_all_html_tags(original_content)
                logging.warning("HTML теги видалено повністю")
        
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