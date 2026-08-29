import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_KEY = os.environ["GROQ_API_KEY"]

app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 CØDÌÈXØÑLY is online!")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are CØDÌÈXØÑLY, a friendly AI assistant."
                    },
                    {
                        "role": "user",
                        "content": update.message.text
                    }
                ],
                "max_tokens": 500
            },
            timeout=60
        )

        data = response.json()

        if response.status_code != 200:
            await update.message.reply_text("❌ AI service error.")
            return

        answer = data["choices"][0]["message"]["content"]
        await update.message.reply_text(answer)

    
       except Exception as e:
    print("ERROR:", repr(e))
    await update.message.reply_text(f"❌ Error: {e}")
  


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
)


@app.route("/")
def home():
    return "CØDÌÈXØÑLY is online 🤖"


@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.process_update(update)

    return "OK"


if __name__ == "__main__":
    import asyncio

    async def main():
        await telegram_app.initialize()
        await telegram_app.start()

        port = int(os.environ.get("PORT", 10000))

        app.run(
            host="0.0.0.0",
            port=port
        )

    asyncio.run(main())