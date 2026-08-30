import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

SECRET = os.environ.get("COMPANION_SECRET", "")

phone = None
telegram = None


@app.get("/")
def health():
    return {"ok": True, "service": "android-companion-relay"}


@app.websocket("/companion")
async def companion(websocket: WebSocket):
    global phone

    if websocket.headers.get("X-Companion-Secret") != SECRET:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    phone = websocket
    print("PHONE CONNECTED")

    try:
        while True:
            message = await websocket.receive_text()
            print("PHONE ->", message)

            if telegram:
                await telegram.send_text(message)

    except WebSocketDisconnect:
        print("PHONE DISCONNECTED")
    finally:
        if phone is websocket:
            phone = None


@app.websocket("/telegram")
async def telegram_ws(websocket: WebSocket):
    global telegram

    if websocket.headers.get("X-Companion-Secret") != SECRET:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    telegram = websocket
    print("TELEGRAM BOT CONNECTED")

    try:
        while True:
            message = await websocket.receive_text()
            print("TELEGRAM ->", message)

            if phone:
                await phone.send_text(message)

    except WebSocketDisconnect:
        print("TELEGRAM DISCONNECTED")
    finally:
        if telegram is websocket:
            telegram = None