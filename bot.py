import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_KEY = os.environ["GROQ_API_KEY"]

OWNER_ID = 7703617341
MODEL = "openai/gpt-oss-20b"

bot_app = Application.builder().token(TOKEN).updater(None).build()
web = Flask(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 CØDÌÈXØÑLY is online!")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    await update.message.reply_text("🧠 Conversation reset.")


async def system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🔒 Owner only.")
        return

    await update.message.reply_text(
        "☁️ CØDÌÈXØÑLY is running on the cloud server."
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        history = context.user_data.setdefault("history", [])

        messages = [
            {
                "role": "system",
                "content": "You are CØDÌÈXØÑLY, a friendly AI assistant."
            }
        ]

        messages.extend(history[-10:])
        messages.append({
            "role": "user",
            "content": update.message.text
        })

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
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
            await update.message.reply_text("❌ AI service error.")
            return

        answer = data["choices"][0]["message"]["content"]

        history.append({
            "role": "user",
            "content": update