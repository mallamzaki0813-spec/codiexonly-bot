from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.get("/")
def health():
    return {"ok": True}

@app.websocket("/companion")
async def companion(websocket: WebSocket):
    await websocket.accept()
    print("CONNECTED")

    try:
        while True:
            message = await websocket.receive_text()
            print("RECEIVED:", message)
            await websocket.send_text(message)
    except WebSocketDisconnect:
        print("DISCONNECTED")