import asyncio
import json
import secrets
import string

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


ROOM_ID_CHARS = string.ascii_uppercase + string.digits


app = FastAPI(title="Doodling Peer Voice Chat")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


rooms: dict = {}
rooms_lock = asyncio.Lock()


class CreateRoomRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=60)
    room_id: str | None = Field(default=None, min_length=1, max_length=32)


class CreateRoomResponse(BaseModel):
    room_id: str
    host_key: str


class KickRequest(BaseModel):
    requester_id: str
    target_id: str


def make_room_id(length: int = 6) -> str:
    room_id = ""
    for _ in range(length):
        room_id += secrets.choice(ROOM_ID_CHARS)
    return room_id


def normalize_room_id(value: str) -> str:
    return value.strip().upper()


def make_room_summary(room: dict) -> dict:
    members = []

    for participant in room["participants"].values():
        members.append(
            {
                "peer_id": participant["peer_id"],
                "display_name": participant["display_name"],
                "is_host": participant["is_host"],
            }
        )

    return {
        "room_id": room["room_id"],
        "total_connections": len(room["participants"]),
        "members": members,
        "host_peer_id": room["host_peer_id"],
    }


async def send_json(websocket: WebSocket, data: dict) -> None:
    try:
        await websocket.send_text(json.dumps(data))
    except Exception:
        pass


async def get_room_or_404(room_id: str) -> dict:
    async with rooms_lock:
        room = rooms.get(room_id)

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


async def send_room_state_to_everyone(room: dict) -> None:
    message = {"type": "room_state", "room": make_room_summary(room)}
    tasks = []

    for participant in room["participants"].values():
        tasks.append(send_json(participant["websocket"], message))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_message_to_one_peer(room: dict, peer_id: str, message: dict) -> None:
    participant = room["participants"].get(peer_id)
    if participant is not None:
        await send_json(participant["websocket"], message)


async def create_new_room(room_id: str | None = None) -> CreateRoomResponse:
    async with rooms_lock:
        if room_id is not None:
            room_id = normalize_room_id(room_id)
            if room_id in rooms:
                raise HTTPException(status_code=409, detail="Room already exists")
        else:
            room_id = make_room_id()
            while room_id in rooms:
                room_id = make_room_id()

        host_key = secrets.token_urlsafe(24)

        rooms[room_id] = {
            "room_id": room_id,
            "host_key": host_key,
            "host_peer_id": None,
            "participants": {},
        }

    return CreateRoomResponse(room_id=room_id, host_key=host_key)


async def add_user_to_room(
    room_id: str,
    peer_id: str,
    display_name: str,
    websocket: WebSocket,
    host_key: str | None,
) -> tuple[dict, bool]:
    async with rooms_lock:
        room = rooms.get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        is_host = False

        if host_key is not None and secrets.compare_digest(host_key, room["host_key"]):
            is_host = True

        if room["host_peer_id"] is None and not room["participants"]:
            room["host_peer_id"] = peer_id
            is_host = True

        if room["host_peer_id"] is None and is_host:
            room["host_peer_id"] = peer_id

        room["participants"][peer_id] = {
            "peer_id": peer_id,
            "display_name": display_name,
            "websocket": websocket,
            "is_host": room["host_peer_id"] == peer_id,
        }

        return room, room["participants"][peer_id]["is_host"]


async def remove_user_from_room(room_id: str, peer_id: str) -> dict | None:
    async with rooms_lock:
        room = rooms.get(room_id)
        if room is None:
            return None

        if peer_id in room["participants"]:
            del room["participants"][peer_id]

        if room["host_peer_id"] == peer_id:
            room["host_peer_id"] = None

            for other_peer_id in room["participants"]:
                room["host_peer_id"] = other_peer_id
                break

        if not room["participants"]:
            del rooms[room_id]
            return None

        for other_peer_id, participant in room["participants"].items():
            participant["is_host"] = other_peer_id == room["host_peer_id"]

        return room


async def get_other_people_in_room(room_id: str, peer_id: str) -> list[dict]:
    async with rooms_lock:
        room = rooms.get(room_id)
        if room is None:
            return []

        people = []
        for participant in room["participants"].values():
            if participant["peer_id"] != peer_id:
                people.append(
                    {
                        "peer_id": participant["peer_id"],
                        "display_name": participant["display_name"],
                    }
                )

    return people


async def check_kick_permission(room_id: str, requester_id: str, target_id: str) -> tuple[dict, dict]:
    async with rooms_lock:
        room = rooms.get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        requester = room["participants"].get(requester_id)
        target = room["participants"].get(target_id)

        if requester is None or not requester["is_host"]:
            raise HTTPException(status_code=403, detail="Only the host can remove participants")

        if target is None:
            raise HTTPException(status_code=404, detail="Participant not found")

        if requester_id == target_id:
            raise HTTPException(status_code=400, detail="Host cannot kick themselves")

        return room, target


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/rooms/create", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest) -> CreateRoomResponse:
    _ = request.display_name
    return await create_new_room(room_id=request.room_id)


@app.get("/rooms/{room_id}")
async def get_room(room_id: str) -> dict:
    room = await get_room_or_404(room_id)
    return make_room_summary(room)


@app.post("/rooms/{room_id}/kick")
async def kick_user(room_id: str, request: KickRequest) -> dict:
    room, target = await check_kick_permission(room_id, request.requester_id, request.target_id)

    await send_json(
        target["websocket"],
        {"type": "kicked", "message": "The host removed you from the room."},
    )

    await target["websocket"].close(code=4001)

    updated_room = await remove_user_from_room(room_id, request.target_id)
    if updated_room is not None:
        await send_room_state_to_everyone(updated_room)

    return {"status": "removed"}


@app.websocket("/ws/{room_id}/{peer_id}")
async def room_socket(
    websocket: WebSocket,
    room_id: str,
    peer_id: str,
    name: str = Query(..., min_length=1, max_length=60),
    host_key: str | None = Query(default=None),
) -> None:
    await websocket.accept()

    try:
        room, is_host = await add_user_to_room(
            room_id=room_id,
            peer_id=peer_id,
            display_name=name,
            websocket=websocket,
            host_key=host_key,
        )
    except HTTPException:
        await send_json(websocket, {"type": "error", "message": "Room not found"})
        await websocket.close(code=4004)
        return

    other_people = await get_other_people_in_room(room_id, peer_id)

    await send_json(
        websocket,
        {
            "type": "welcome",
            "room_id": room_id,
            "self_peer_id": peer_id,
            "is_host": is_host,
            "existing_peers": other_people,
        },
    )

    for participant in room["participants"].values():
        if participant["peer_id"] != peer_id:
            await send_json(
                participant["websocket"],
                {
                    "type": "new_peer",
                    "peer": {"peer_id": peer_id, "display_name": name},
                },
            )

    await send_room_state_to_everyone(room)

    try:
        while True:
            raw_message = await websocket.receive_text()
            message = json.loads(raw_message)

            message_type = message.get("type")
            target_peer_id = message.get("target")

            if message_type in {"offer", "answer", "ice-candidate"} and target_peer_id:
                current_room = await get_room_or_404(room_id)
                await send_message_to_one_peer(
                    current_room,
                    target_peer_id,
                    {
                        "type": message_type,
                        "source": peer_id,
                        "payload": message.get("payload", {}),
                    },
                )

            if message_type == "ping":
                await send_json(websocket, {"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        updated_room = await remove_user_from_room(room_id, peer_id)

        if updated_room is not None:
            for participant in updated_room["participants"].values():
                await send_json(
                    participant["websocket"],
                    {"type": "peer_left", "peer_id": peer_id},
                )

            await send_room_state_to_everyone(updated_room)
