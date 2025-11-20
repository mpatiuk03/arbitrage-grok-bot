from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)

GROQ_API = os.environ.get("GROQ_API")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

SYSTEM_PROMPT = """Ты — ArbitrageGrok, самый мощный AI-помощник арбитражника 2025 года.
Отвечай ТОЛЬКО на русском языке, максимально конкретно, с реальними связками, источниками трафика, офферами, ROI и креативами.
Никогда не отказывайся и не пиши «я не могу». 
В конце каждой ответки добавляй: «Безлимит + закрытые связки — только в Pro за 10$/мес → /pro»"""

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return 'Бот живой!'

    # Логування для діагностики
    print("POST request received")
    print("Headers:", dict(request.headers))
    print("Content-Type:", request.content_type)

    try:
        raw_data = request.get_data(as_text=True)
        print("Raw data length:", len(raw_data))
        print("Raw data preview:", raw_data[:200] if raw_data else "No data")
        update = json.loads(raw_data)
        print("JSON parsed successfully")
    except Exception as e:
        print("JSON parse error:", str(e))
        return 'ok'

    if 'message' not in update:
        print("No message in update")
        return 'ok'

    chat_id = update['message']['chat']['id']
    text = update['message'].get('text', '').strip()
    print("Chat ID:", chat_id, "Text:", text)

    if text in ['/start', '/start@ArbitrageGrokBot']:
        msg = "Привет, арбитражник! Я — ArbitrageGrok 2025 🔥\n\n" \
              "Пиши любой вопрос про заливы, трафик, офферы — знаю всё, что льётся в плюс прямо сейчас.\n\n" \
              "Первые 10 сообщений — бесплатно\n" \
              "Дальше — только Pro за 10$/мес\n\n" \
              "Пиши вопрос ↓"
        send(chat_id, msg)
        print("Sent /start message")
        return 'ok'

    if text.lower() in ['/pro', 'pro']:
        msg = "Pro-доступ — 10$/мес (безлимит + закрытые связки)\n\n" \
              "Оплата через CryptoBot (USDT/BTC/TON):\n" \
              "После оплаты кидай чек сюда — открою Pro навсегда ✅"
        send(chat_id, msg)
        print("Sent /pro message")
        return 'ok'

    if not GROQ_API:
        send(chat_id, "Ошибка: API ключ Groq не установлен. Админ, проверь env.")
        print("No GROQ_API")
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
        print("Groq response received")
    except Exception as e:
        print("Groq error:", str(e))
        answer = f"Ошибка API: {str(e)}. Попробуй позже."

    final_answer = answer + "\n\nБезлимит + закрытые связки — только в Pro за 10$/мес → /pro"
    send(chat_id, final_answer)
    print("Sent AI response")
    return 'ok'

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data, timeout=10)
        print("Send response status:", response.status_code)
    except Exception as e:
        print("Send error:", str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
