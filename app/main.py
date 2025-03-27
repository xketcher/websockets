from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from pydantic import BaseModel
import asyncio import Form

app = FastAPI()

# Token Authentication
WS_TOKEN = "token1"
POST_TOKEN = "token2"

# Room Storage
rooms = {}  # { "room_name": set([websocket1, websocket2, ...]) }


class Message(BaseModel):
    message: str


@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str, authorization: str = Header(None)):
    """ WebSocket connection for joining a chat room """
    # Validate token
    if authorization != f"Bearer {WS_TOKEN}":
        await websocket.close(code=1008)
        return

    await websocket.accept()

    # Add client to room
    rooms.setdefault(room, set()).add(websocket)

    try:
        async for _ in websocket.iter_text():  # Efficient listening
            pass
    except WebSocketDisconnect:
        # Remove disconnected client
        rooms[room].discard(websocket)
        if not rooms[room]:  # If room is empty, delete it
            del rooms[room]




@app.post("/ws/send/{room}")
async def send_message(room: str, message: str = Form(...), authorization: str = Header(None)):
    """Send a message using x-www-form-urlencoded"""
    if authorization != f"Bearer {POST_TOKEN}":
        raise HTTPException(403, "Invalid token")
    
    if room not in rooms:
        raise HTTPException(404, "Room not found")

    disconnected = []
    for ws in rooms[room]:
        try:
            await ws.send_text(message)
        except:
            disconnected.append(ws)

    for ws in disconnected:
        rooms[room].discard(ws)

    return {"message": "Sent", "clients": len(rooms[room])}

@app.get("/ws/rooms")
async def list_rooms():
    """ API to list all active rooms and their client counts """
    return {room: len(clients) for room, clients in rooms.items()}


@app.get("/ws/clients/{room}")
async def list_clients_in_room(room: str):
    """ API to list the number of connected clients in a specific room """
    if room not in rooms:
        raise HTTPException(404, "Room not found")
    return {"room": room, "clients": len(rooms[room])}
