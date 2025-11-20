from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)

GROQ_API = os.environ.get("GROQ_API")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

SYSTEM_PROMPT = """Ты — ArbitrageGrok, самый мощный AI-помощник арбитражника 2025 года.
Отвечай ТОЛЬКО на русском языке, максимально конкретно, с реальными связками, источниками трафика, офферами, ROI и креативами.
Никогда не отказывайся и не пиши «я не могу». 
В конце каждой ответки добавляй: «Безлимит + закрытые связки — только в Pro за 10$/мес → /pro»"""

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return 'Бот живой!'

    try:
        # Фікс для парсингу JSON — використовуємо json.loads
        raw_data = request.get_data(as_text=True)
        update = json.loads(raw_data)
    except:
        return 'ok'

    if 'message' not in update:
        return 'ok'

    chat_id = update['message']['chat']['id']
    text = update['message'].get('text', '').strip()

    if text in ['/start', '/start@ArbitrageGrokBot']:
        msg = "Привет, арбитражник! Я — ArbitrageGrok 2025 🔥\n\n" \
              "Пиши любой вопрос про заливы, трафик, офферы — знаю всё, что льётся в плюс прямо сейчас.\n\n" \
              "Первые 10 сообщений — бесплатно\n" \
              "Дальше — только Pro за 10$/мес\n\n" \
              "Пиши вопрос ↓"
        send(chat_id, msg)
        return 'ok'

    if text.lower() in ['/pro', 'pro']:
        msg = "Pro-доступ — 10$/мес (безлимит + закрытые связки)\n\n" \
              "Оплата через CryptoBot (USDT/BTC/TON):\n" \
              "После оплаты кидай чек сюда — открою Pro навсегда ✅"
        send(chat_id, msg)
        return 'ok'

    if not GROQ_API:
        send(chat_id, "Ошибка: API ключ Groq не установлен. Админ, проверь env.")
        return 'ok'

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
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          json=payload,
                          headers={"Authorization": f"Bearer {GROQ_API}", "Content-Type": "application/json"},
                          timeout=30)
        r.raise_for_status()
        answer = r.json()['choices'][0]['message']['content']
    except Exception as e:
        answer = f"Ошибка API: {str(e)}. Попробуй позже."

    final_answer = answer + "\n\nБезлимит + закрытые связки — только в Pro за 10$/мес → /pro"
    send(chat_id, final_answer)
    return 'ok'

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass  # Ігноруємо помилки відправки

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
