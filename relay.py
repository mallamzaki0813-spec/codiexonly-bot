import os
import hashlib

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

SECRET = os.environ.get("COMPANION_SECRET", "")
print("SERVER SECRET LENGTH:", len(SECRET))
print("SERVER SECRET HASH:", hashlib.sha256(SECRET.strip().encode()).hexdigest())
phone = None
telegram = None


@app.get("/")
async def health():
    return {
        "ok": True,
        "service": "android-companion-relay"
    }


@app.websocket("/companion")
async def companion(websocket: WebSocket):
    global phone

    incoming_secret = websocket.headers.get(
        "X-Companion-Secret",
        ""
    )

    print(
        "COMPANION SECRET HASH:",
        hashlib.sha256(incoming_secret.encode()).hexdigest()
    )

    print(
        "SERVER SECRET HASH:",
        hashlib.sha256(SECRET.encode()).hexdigest()
    )

    print(
        "SECRET MATCH:",
        incoming_secret == SECRET
    )

    if incoming_secret != SECRET:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    phone = websocket

    print("PHONE CONNECTED")

    try:
        while True:
            message = await websocket.receive_text()

            print("PHONE ->", message)

            if telegram is not None:
                try:
                    await telegram.send_text(message)

                except Exception as e:
                    print(
                        "Failed to send result to Telegram:",
                        e
                    )

    except WebSocketDisconnect:
        print("PHONE DISCONNECTED")

    except Exception as e:
        print(
            "PHONE ERROR:",
            type(e).__name__,
            str(e)
        )

    finally:
        if phone is websocket:
            phone = None


@app.websocket("/telegram")
async def telegram_ws(websocket: WebSocket):
    global telegram, phone

    incoming_secret = websocket.headers.get(
        "X-Companion-Secret",
        ""
    )

    print(
        "TELEGRAM SECRET MATCH:",
        incoming_secret == SECRET
    )

    if incoming_secret != SECRET:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    telegram = websocket

    print("TELEGRAM BOT CONNECTED")

    try:
        while True:
            message = await websocket.receive_text()

            print("TELEGRAM ->", message)

            if phone is None:
                await websocket.send_text(
                    '{"ok": false, "message": "Android Companion is not connected."}'
                )
                continue

            try:
                await phone.send_text(message)

            except Exception as e:
                print(
                    "Failed to send command to phone:",
                    e
                )

                phone = None

                await websocket.send_text(
                    '{"ok": false, "message": "Failed to reach Android Companion."}'
                )

    except WebSocketDisconnect:
        print("TELEGRAM DISCONNECTED")

    except Exception as e:
        print(
            "TELEGRAM ERROR:",
            type(e).__name__,
            str(e)
        )

    finally:
        if telegram is websocket:
            telegram = None