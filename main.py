from flask import Flask, request, Response
import requests
import os
import json

app = Flask(__name__)

GROQ_API = os.environ.get("GROQ_API")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

SYSTEM_PROMPT = """Ты — ArbitrageGrok, самый мощный AI-помощник арбитражника 2025 года.
Отвечай ТОЛЬКО на русском языке, максимально конкретно, с реальными связками, источниками трафика, офферами, ROI и креативами.
В конце каждой ответки добавляй: «Безлимит + закрытые связки — только в Pro за 10$/мес → /pro»"""

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return 'ArbitrageGrok 2025 — Бот живой! 🚀', 200

    raw = request.get_data(as_text=True)
    if not raw:
        return 'ok', 200

    try:
        update = json.loads(raw)
    except:
        return 'ok', 200

    if 'message' not in update:
        return 'ok', 200

    chat_id = update['message']['chat']['id']
    text = update['message'].get('text', '').strip()

    if text.startswith('/start'):
        msg = "Привет, арбитражник! Я — ArbitrageGrok 2025 🔥\n\nПиши любой вопрос про заливы, трафик, офферы — знаю всё, что льётся в плюс прямо сейчас.\n\nПервые 10 сообщений — бесплатно\nДальше — только Pro за 10$/мес\n\nПиши вопрос ↓"
        send(chat_id, msg)
        return 'ok', 200

    if text.lower() in ['/pro', 'pro']:
        msg = "Pro-доступ — 10$/мес\nОплата через @CryptoBot (USDT/BTC/TON)\nКидай чек — открою безлимит навсегда ✅"
        send(chat_id, msg)
        return 'ok', 200

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
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {GROQ_API}"}, timeout=50)
        r.raise_for_status()
        answer = r.json()['choices'][0]['message']['content']
    except:
        answer = "Сервер чуть тормозит, попробуй через 20 сек."

    final = answer + "\n\nБезлимит + закрытые связки — только в Pro за 10$/мес → /pro"
    send(chat_id, final)
    return 'ok', 200

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": text[:4096], "parse_mode": "HTML"}, timeout=10)
    except:
        pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
