import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

SECRET = os.environ.get("COMPANION_SECRET")

@app.websocket("/companion")
async def companion(websocket: WebSocket):
    if websocket.headers.get("X-Companion-Secret") != SECRET:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass