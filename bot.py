import os
import json
import asyncio
import requests
import websockets

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_KEY = os.environ["GROQ_API_KEY"]

RELAY_URL = "wss://codiexonly-relay.onrender.com/telegram"
COMPANION_SECRET = os.environ.get("COMPANION_SECRET", "")

# Your Render Web Service URL.
# Put this in Render as WEBHOOK_URL.
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

print("WEBHOOK_URL configured:", bool(WEBHOOK_URL))

PORT = int(os.environ.get("PORT", "10000"))
WEBHOOK_PATH = "/telegram-webhook"

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are CØDÌÈXØÑLY, a friendly AI assistant on Telegram.
Your name is CØDÌÈXØÑLY.
Do not identify yourself as Groq, OpenAI, GPT, or any other model unless specifically asked what technology powers you.
Talk naturally and helpfully.
"""

relay_ws = None
relay_lock = asyncio.Lock()


async def connect_relay():
    global relay_ws

    while True:
        ws = None

        try:
            print("🔗 Connecting Telegram bot to Android relay...")

            ws = await websockets.connect(
                RELAY_URL,
                additional_headers={
                    "X-Companion-Secret": COMPANION_SECRET
                },
                open_timeout=30,
                ping_interval=20,
                ping_timeout=20,
            )

            relay_ws = ws

            print("🔗 Telegram bot connected to Android relay.")

            while relay_ws is ws:
                await asyncio.sleep(10)

        except Exception as e:
            print("⚠️ Relay connection lost:", type(e).__name__, str(e))

            if ws is not None and relay_ws is ws:
                relay_ws = None

            await asyncio.sleep(5)


async def send_companion_command(command):
    global relay_ws

    async with relay_lock:
        if relay_ws is None:
            return {
                "ok": False,
                "message": "Android Companion is not connected."
            }

        try:
            await relay_ws.send(command)
            reply = await relay_ws.recv()

            try:
                return json.loads(reply)
            except json.JSONDecodeError:
                return {
                    "ok": True,
                    "message": reply
                }

        except Exception as e:
            relay_ws = None

            return {
                "ok": False,
                "message": "Android relay connection failed: " + str(e)
            }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []

    await update.message.reply_text(
        "🤖 CØDÌÈXØÑLY AI is online!"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    context.user_data.pop("call_pending", None)

    await update.message.reply_text(
        "🧠 Conversation reset."
    )


async def battery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = await send_companion_command("battery")

    if not result.get("ok"):
        await update.message.reply_text(
            "❌ Battery request failed:\n"
            + str(
                result.get(
                    "message",
                    result.get("error", "Unknown error")
                )
            )
        )
        return

    battery_data = result.get("battery")

    if not battery_data:
        await update.message.reply_text(
            "❌ No battery information was returned."
        )
        return

    percentage = battery_data.get("percentage", "Unknown")
    status = battery_data.get("status", "Unknown")
    plugged = battery_data.get("plugged", "Unknown")

    await update.message.reply_text(
        f"🔋 Battery: {percentage}%\n"
        f"⚡ Status: {status}\n"
        f"🔌 Plugged: {plugged}"
    )


async def call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📞 Usage:\n/call <number>\n\n"
            "Example:\n/call 08012345678"
        )
        return

    number = " ".join(context.args).strip()

    context.user_data["call_pending"] = number

    await update.message.reply_text(
        f"📞 Call request prepared for:\n{number}\n\n"
        "Reply with /confirmcall to place the call, "
        "or /cancelcall to cancel it."
    )


async def confirm_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = context.user_data.get("call_pending")

    if not number:
        await update.message.reply_text(
            "❌ There is no pending call."
        )
        return

    result = await send_companion_command(
        "call:" + number
    )

    if result.get("ok"):
        await update.message.reply_text(
            "📞 Call request sent to the Android Companion."
        )
    else:
        await update.message.reply_text(
            "❌ Call request failed:\n"
            + str(
                result.get(
                    "message",
                    result.get("error", "Unknown error")
                )
            )
        )

    context.user_data.pop("call_pending", None)


async def cancel_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("call_pending", None)

    await update.message.reply_text(
        "❌ Call cancelled."
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        history = context.user_data.setdefault("history", [])

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        messages.extend(history[-10:])

        messages.append({
            "role": "user",
            "content": update.message.text
        })

        response = requests.post(
            API_URL,
            headers={
                "Authorization": "Bearer " + GROQ_KEY,
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
                "❌ Groq API error:\n" + str(data)
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

    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "❌ Groq timed out."
        )

    except Exception as e:
        await update.message.reply_text(
            "❌ Error: " + str(e)
        )


async def post_init(application):
    asyncio.create_task(connect_relay())


app = (
    Application.builder()
    .token(TELEGRAM_TOKEN)
    .post_init(post_init)
    .build()
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("battery", battery))
app.add_handler(CommandHandler("call", call))
app.add_handler(CommandHandler("call", call))
app.add_handler(CommandHandler("confirmcall", confirm_call))
app.add_handler(CommandHandler("cancelcall", cancel_call))
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat
    )
)

print("🤖 CØDÌÈXØÑLY AI is starting in webhook mode...")
print("🚀 Starting webhook...")
print(f"🌐 Listening on port {PORT}")

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"),
        webhook_url=WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH,
        drop_pending_updates=True,
    )     
        
   

     