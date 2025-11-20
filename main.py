import os
import json
import requests
import logging
import time
from flask import Flask, request, abort

# --- Настройка логирования (для отладки в среде Render) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Конфигурация из переменных окружения ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_MODEL = 'llama-3.1-70b-instant' # Запрошенная модель
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# --- Groq System Prompt ---
SYSTEM_PROMPT = (
    "Ты — ArbitrageGrok, самый мощный AI-помощник арбитражника 2025 года. "
    "Отвечай ТОЛЬКО на русском языке, максимально конкретно, с реальными связками, "
    "источниками трафика, офферами, ROI и креативами. "
    "Никогда не отказывайся и не пиши «я не могу». "
    "В конце каждого ответа добавляй: «Безлимит + закрытые связки — только в Pro за 10$/мес → /pro»"
)

# --- Инициализация Flask приложения ---
app = Flask(__name__)

if not BOT_TOKEN or not GROQ_API_KEY:
    logger.error("BOT_TOKEN або GROQ_API_KEY не задані в змінних оточення.")

# --- Вспомогательные функции ---

def send_message(chat_id: int, text: str):
    """Отправляет сообщение через Telegram Bot API."""
    method = 'sendMessage'
    url = TELEGRAM_API_URL + method
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status() 
    except requests.exceptions.Timeout:
        logger.error(f"Telegram API: Перевищено час очікування при відправці повідомлення в чат {chat_id}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram API: Помилка при відправці повідомлення в чат {chat_id}: {e}")

def get_groq_response(prompt: str) -> str:
    """Получает ответ от Groq API."""
    if not GROQ_API_KEY:
        return "Помилка: Ключ Groq API не заданий. Зверніться до адміністратора."

    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': GROQ_MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 1500
    }
    
    try:
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        response = requests.post(groq_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('choices'):
            return data['choices'][0]['message']['content']
        else:
            logger.warning(f"Groq API: Невірний формат відповіді: {data}")
            return "Вибачте, Groq API повернув некоректну відповідь. Спробуйте ще раз."

    except requests.exceptions.Timeout:
        logger.error("Groq API: Перевищено час очікування відповіді.")
        return "Вибачте, перевищено час очікування відповіді від AI. Спробуйте ще раз через хвилину."
    except requests.exceptions.RequestException as e:
        logger.error(f"Groq API: Помилка запиту: {e}")
        return f"Вибачте, сталася помилка при зверненні до Groq API: {e}."
    except Exception as e:
        logger.error(f"Groq API: Непередбачена помилка: {e}")
        return "Вибачте, сталася внутрішня помилка сервера AI."

def handle_message(chat_id: int, text: str):
    """Обрабатывает входящее сообщение и команды."""
    text_lower = text.lower().strip()
    
    if text_lower == '/start':
        response_text = (
            "Привет, арбитражник! Я — ArbitrageGrok 2025 🔥\n"
            "Пиши любой вопрос про заливы, трафик, офферы — знаю всё, что льётся в плюс прямо сейчас.\n"
            "Первые 10 сообщений — бесплатно. Дальше — только Pro за 10$/мес (безлимит + закрытые связки)\n"
            "Пиши свой вопрос ↓"
        )
        send_message(chat_id, response_text)
    
    elif text_lower == '/pro' or text_lower == 'pro':
        response_text = (
            "Pro-доступ — 10$/мес\n"
            "Оплата через @CryptoBot (USDT/BTC/TON)\n"
            "После оплаты кидай чек сюда — открою безлимит навсегда ✅"
        )
        send_message(chat_id, response_text)
        
    else:
        ai_response = get_groq_response(text)
        send_message(chat_id, ai_response)

# --- Flask Роуты ---

@app.route('/', methods=['GET', 'POST'])
def webhook():
    """Обработка вебхука Telegram."""
    
    if request.method == 'GET':
        return "ArbitrageGrok 2025 — Бот живой! 🚀", 200

    if request.method == 'POST':
        if not request.data:
            logger.info("Получен пустой POST-запрос.")
            return 'ok', 200, {'Content-Type': 'text/plain'}

        try:
            update = request.get_json(force=True)
            
            if not update:
                logger.warning("Не вдалося розпарсити тіло POST-запиту як JSON.")
                return 'ok', 200, {'Content-Type': 'text/plain'}

        except Exception as e:
            logger.error(f"Помилка парсингу JSON: {e}")
            return 'ok', 200, {'Content-Type': 'text/plain'}
            
        try:
            message = update.get('message')
            if message:
                chat_id = message['chat']['id']
                text = message.get('text', '') 

                if text:
                    handle_message(chat_id, text)
                
            else:
                pass

        except Exception as e:
            logger.error(f"Непередбачена помилка в обробнику: {e}")
            
        return 'ok', 200, {'Content-Type': 'text/plain'}

@app.route('/ping', methods=['GET'])
def ping():
    """Ендпоінт для Uptimerobot (9)."""
    return "pong", 200

if __name__ == '__main__':
    logger.info("Запуск Flask в режимі відладки (тільки для локальної розробки).")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
