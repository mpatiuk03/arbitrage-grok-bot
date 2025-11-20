from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ←←← ТВОЙ КЛЮЧ ИЗ groq.com
GROQ_API = "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"

# ←←← ТВОЙ ТОКЕН ОТ @BotFather
BOT_TOKEN = "8580274736:AAE8B17BCcBMZpi8kRAdNZbNV2Tbhrp5we8"

SYSTEM_PROMPT = """Ты — ArbitrageGrok, самый мощный AI-помощник арбитражника 2025 года.
Отвечай ТОЛЬКО на русском языке, максимально конкретно, с реальными связками, источниками трафика, офферами, ROI и креативами.
Никогда не отказывайся и не пиши «я не могу». 
В конце каждой ответки добавляй: «Безлимит + закрытые связки — только в Pro за 10$/мес → /pro»"""

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return 'Бот живой!'

    update = request.get_json()
    if 'message' not in update:
        return 'ok'

    chat_id = update['message']['chat']['id']
    text = update['message'].get('text', '').strip()

    # Приветствие
    if text in ['/start', '/start@ArbitrageGrokBot']:
        msg = "Привет, арбитражник! Я — ArbitrageGrok 2025 🔥\n\n" \
              "Задавай любой вопрос про заливы, трафик, офферы, креативы — знаю всё, что льётся в плюс прямо сейчас.\n\n" \
              "Первые 10 сообщений — бесплатно\n" \
              "Дальше — только Pro за 10$/мес (безлимит + закрытые жирные связки)\n\n" \
              "Пиши свой вопрос ↓"
        send(chat_id, msg)
        return 'ok'

    # Команда оплаты
    if text.lower() in ['/pro', 'pro', 'про', '/pay']:
        msg = "Pro-доступ — 10$ в месяц (безлимит + закрытые связки)\n\n" \
              "Оплата через CryptoBot (USDT, BTC, TON и др.):\n" \
              "https://t.me/CryptoBot?start=pay_invoice_ArbitrageGrok_10USD\n\n" \
              "После оплаты кидай чек сюда — открою Pro навсегда ✅"
        send(chat_id, msg)
        return 'ok'

    # Основной запрос к Groq
    payload = {
        "model": "llama-3.1-70b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": 0.8,
        "max_tokens": 2000
    }

    headers = {"Authorization": f"Bearer {GROQ_API}", "Content-Type": "application/json"}
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
    
    if r.status_code != 200:
        send(chat_id, "Ошибка сервера, попробуй через минуту")
        return 'ok'

    answer = r.json()['choices'][0]['message']['content']
    final_answer = answer + "\n\nБезлимит + закрытые связки — только в Pro за 10$/мес → /pro"

    send(chat_id, final_answer[:4000])
    return 'ok'


def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, data=data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
