from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
rooms = {}

@app.websocket("/ws/{room}")
async def chat(websocket: WebSocket, room: str):
    await websocket.accept()
    rooms.setdefault(room, []).append(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            for ws in rooms[room]:
                await ws.send_text(msg)
    except WebSocketDisconnect:
        rooms[room].remove(websocket)
        if not rooms[room]: del rooms[room]
