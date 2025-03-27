from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Form
from pydantic import BaseModel
import asyncio

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
async def send_message(
    room: str,
    data: Message = None,  # For JSON body data
    message: str = Form(None),  # For x-www-form-urlencoded data
    authorization: str = Header(None)
):
    """ API to send a message to all clients in a room """
    # Validate token
    if authorization != f"Bearer {POST_TOKEN}":
        raise HTTPException(403, "Invalid token")
    
    # Check if room exists
    if room not in rooms:
        raise HTTPException(404, "Room not found")

    # Determine the message type (either JSON or form data)
    final_message = data.message if data else message

    # If no message is provided, raise an error
    if not final_message:
        raise HTTPException(400, "Message content cannot be empty")

    # Send message to all clients
    disconnected = []
    for ws in rooms[room]:
        try:
            await ws.send_text(final_message)
        except:
            disconnected.append(ws)  # Mark disconnected clients

    # Remove disconnected clients
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
