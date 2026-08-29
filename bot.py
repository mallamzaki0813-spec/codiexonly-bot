import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_KEY = os.environ["GROQ_API_KEY"]

OWNER_ID = 7703617341

MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are CØDÌÈXØÑLY, a friendly AI assistant on Telegram.
Your name is CØDÌÈXØÑLY.
Talk naturally and helpfully.
"""

app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    await update.message.reply_text(
        "🤖 CØDÌÈXØÑLY is online!"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    await update.message.reply_text("🧠 Conversation reset.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        history = context.user_data.setdefault("history", [])

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        messages.extend(history[-10:])

        messages.append({
            "role": "user",
            "content": update.message.text
        })

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800
            },
            timeout=60
        )

        data = response.json()

        if response.status_code != 200:
            await update.message.reply_text(
                "❌ Groq error."
            )
            return

        answer = data["choices"][0]["message"]["content"]

        history.append({
            "role": "user",
            "content": update.message.text
        })

        history.append({
            "role": "assistant",
            "content": answer
        })

        context.user_data["history"] = history[-10:]

        await update.message.reply_text(answer)

    except Exception:
        await update.message.reply_text(
            "❌ Something went wrong. Try again."
        )

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("reset", reset))
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

        from werkzeug.serving import run_simple
        run_simple(
            "0.0.0.0",
            port,
            app,
            use_reloader=False
        )

    asyncio.run(main())
