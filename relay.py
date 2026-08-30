import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

SECRET = os.environ.get("COMPANION_SECRET")

@app.websocket("/companion")
async def companion(websocket: WebSocket):
    await websocket.accept()

    try:
        if websocket.query_params.get("secret") != SECRET:
            await websocket.close(code=1008)
            return

        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)

    except WebSocketDisconnect:
        pass