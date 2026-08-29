import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_KEY = os.environ["GROQ_API_KEY"]

app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).updater(None).build()


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
            print("GROQ ERROR:", data)
            await update.message.reply_text("❌ AI service error.")
            return

        answer = data["choices"][0]["message"]["content"]
        await update.message.reply_text(answer)

    except Exception as e:
        print("CHAT ERROR:", repr(e))
        await update.message.reply_text("❌ Something went wrong.")


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
)


@app.route("/")
def home():
    return "CØDÌÈXØÑLY is online 🤖"


@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = request.get_json()
        update = Update.de_json(data, telegram_app.bot)

        await telegram_app.process_update(update)

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))
        return "ERROR", 500


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
        
   

               
        
   

     