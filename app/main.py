from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
rooms = {}

# Allowed tokens for connection
VALID_TOKENS = {
    "dy467ghxxZg56SFYI_432FGdfP": True,  # This token can send messages
    "57ghuGui56xgjjSfjppkjuu356sfgSrgh": False  # This token can only connect
}

@app.websocket("/ws/{room}")
async def chat(websocket: WebSocket, room: str):
    token = websocket.headers.get("Authorization", "").replace("Bearer ", "")

    # Token မမှန်ရင် ချိတ်မပေးဘူး
    if token not in VALID_TOKENS:
        await websocket.close()
        return

    await websocket.accept()
    rooms.setdefault(room, []).append((websocket, token))

    try:
        while True:
            msg = await websocket.receive_text()
            sender_token = next((t for ws, t in rooms[room] if ws == websocket), "")

            # Token မှန်မှသာ message ပို့ခွင့်ပြုမယ်
            if VALID_TOKENS.get(sender_token, False):
                for ws, _ in rooms[room]:
                    await ws.send_text(msg)
    except WebSocketDisconnect:
        rooms[room] = [(ws, t) for ws, t in rooms[room] if ws != websocket]
        if not rooms[room]:
            del rooms[room]
