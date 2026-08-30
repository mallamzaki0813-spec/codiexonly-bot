import os
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_KEY = os.environ["GROQ_KEY"]

PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://codiexonly-bot.onrender.com/webhook"

application = Application.builder().token(TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 CØDÌÈXØÑLY is online!")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are CØDÌÈXØÑLY, a helpful AI assistant.",
                    },
                    {
                        "role": "user",
                        "content": update.message.text,
                    },
                ],
                "max_tokens": 500,
            },
            timeout=60,
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


application.add_handler(CommandHandler("start", start))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
)


if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )
   

               
        
   

     