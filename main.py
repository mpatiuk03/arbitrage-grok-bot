from flask import Flask, Response
import requests
import os
import json

app = Flask(__name__)

GROQ_API = os.environ.get("GROQ_API")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

SYSTEM_PROMPT = """Ты — ArbitrageGrok, самый мощный AI-помощник арбітражника 2025 года.
Отвечай ТОЛЬКО на русском языке, максимально конкретно, с реальными связками, источниками трафика, офферами, ROI и креативами.
Никогда не отказывайся и не пиши «я не могу». 
В конце каждой ответки добавляй: «Безлимит + закрытые связки — только в Pro за 10$/мес → /pro»"""

@app.route('/ping', methods=['GET'])
def ping():
    return 'pong', 200

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return Response('ArbitrageGrok 2025 — Бот живой! 🚀', status=200, mimetype='text/plain')

    # Завжди повертаємо 200, навіть на помилках (Telegram вимагає)
    response = Response('ok', status=200, mimetype='text/plain')

    # Обробка порожнього body (Telegram тест)
    raw_data = request.get_data(as_text=True)
    if not raw_data or len(raw_data) < 10:
        return response

    try:
        update = json.loads(raw_data)
    except json.JSONDecodeError:
        return response

    if 'message' not in update:
        return response

    chat_id = update['message']['chat']['id']
    text = update['message'].get('text', '').strip()

    # /start
    if text and text.split()[0] in ['/start', '/start@ArbitrageGrokBot']:
        msg = ("Привет, арбитражник! Я — ArbitrageGrok 2025 🔥\n\n"
               "Пиши любой вопрос про заливы, трафик, офферы — знаю всё, что льётся в плюс прямо сейчас.\n\n"
               "Первые 10 сообщений — бесплатно\n"
               "Дальше — только Pro за 10$/мес (безлимит + закрытые связки)\n\n"
               "Пиши свой вопрос ↓")
        send_message(chat_id, msg)
        return response

    # /pro
    if text and text.lower() in ['/pro', 'pro']:
        msg = ("Pro-доступ — 10$/мес\n\n"
               "Оплата через @CryptoBot (USDT/BTC/TON)\n"
               "После оплаты кидай чек сюда — открою безлимит навсегда ✅")
        send_message(chat_id, msg)
        return response

    # Groq
    if not text:
        return response

    payload = {
        "model": "llama-3.1-70b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": 0.8,
        "max_tokens": 2000
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {GROQ_API}"},
            timeout=60
        )
        r.raise_for_status()
        answer = r.json()['choices'][0]['message']['content']
    except:
        answer = "Сервер немного тормозит, попробуй через 30 секунд."

    final = answer + "\n\nБезлимит + закрытые связки — только в Pro за 10$/мес → /pro"
    send_message(chat_id, final)
    return response

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
