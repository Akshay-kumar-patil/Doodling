from fastapi import FastAPI,WebSocket,WebSocketDisconnect
import uvicorn
import manager
import json

app=FastAPI()

# it stores all the active connection of websocket
# { "username": websocket_object } 
active_connections:dict[str,WebSocket] ={}

def validate_message(msg: dict) -> bool:
    if not isinstance(msg, dict):
        return False

    if "type" not in msg or "data" not in msg:
        return False

    if msg["type"] == "start":
        return (
            isinstance(msg["data"], dict)
            and "total_time" in msg["data"]
            and "total_rounds" in msg["data"]
        )

    if msg["type"] == "word_selected":
        return (
            isinstance(msg["data"], dict)
            and "select_word" in msg["data"]
        )

    if msg["type"] == "draw":
        return (
            isinstance(msg["data"], dict)
            and "x" in msg["data"]
            and "y" in msg["data"]
            and "color" in msg["data"]
            and "size" in msg["data"]
        )

    if msg["type"] == "chat":
        return (
            isinstance(msg["data"], dict)
            and "text" in msg["data"]
        )

    return False

# when host create room
@app.post("/Host/create-room/{room_id}") 
async def host_create_room(room_id,username,total_rounds,total_time) ->dict :
    connect=await manager.create_room(room_id=room_id,host_username=username)
    if connect["success"] == True:
        return {"message": "room created successfully"}
    else:
        return {"message":"room already exists"}


@app.websocket("/ws/new-join/{room_id}/{username}")
async def websocket_endpoint(websocket:WebSocket,username:str,room_id:str):
    await websocket.accept()
    active_connections[username]=websocket
    print(f"Player {username} has been added")
    join = await manager.join_room(room_id=room_id,username=username)

    if join["success"] == True:
        await manager.broadcast(room_id, {"message": f"player {username} joined"}, active_connections)
    else:
        await websocket.send_json({"error": join["error"]})
        active_connections.pop(username, None)
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            is_valid=validate_message(msg)
            if not is_valid:
                await websocket.send_json({"message": "invalid message"})
                continue
            
            if msg["type"] == "start":
                start = await manager.start_round(
                    room_id=room_id,
                    total_time=msg["data"]["total_time"],
                    total_rounds=msg["data"]["total_rounds"],
                )

                if start["success"] == False:
                    await websocket.send_json({"error": start["error"]})
                    continue
                
                drawer = start["drawer"]
                word_choices = start["word_choices"]

                await manager.send_to_one(drawer,{"word_choices": word_choices}, active_connections)
                await manager.broadcast(room_id, {"hint": "_ _ _ _ _"}, active_connections)
                await manager.broadcast(room_id, {"type": "start", "drawer": drawer}, active_connections)

            elif msg["type"] == "word_selected":
                select = await manager.select_word(
                    room_id=room_id,
                    choosen_word=msg["data"]["select_word"],
                )
                
                if not select["success"] :
                    await websocket.send_json({"error": select["error"]})
                    continue
                
                drawer = manager.rooms[room_id]["drawer"]
                word=select["word"]
                await manager.send_to_one(drawer, {"word": word}, active_connections)
                await manager.broadcast(
                    room_id,
                    {"hint": manager.get_word_hint(word)},
                    active_connections,
                )


            elif msg["type"] == "draw":
                
                await manager.broadcast_except(
                    room_id,
                    username,
                    {
                        "type": "draw",
                        "x": msg["data"]["x"],
                        "y": msg["data"]["y"],
                        "color": msg["data"]["color"],
                        "size": msg["data"]["size"],
                    },
                    active_connections,
                )

                
            elif msg["type"] == "chat":
                guess_result = await manager.handle_guess(
                    room_id,
                    username,
                    msg["data"]["text"],
                    active_connections,
                )

                if not guess_result["success"]:
                    await websocket.send_json({"error": guess_result["error"]})
                    continue

                if guess_result.get("correct"):
                    await manager.broadcast(
                        room_id,
                        {
                            "message": f"{username} guessed correctly! +{guess_result['points']} points"
                        },
                        active_connections,
                    )

                    await manager.broadcast(
                        room_id,
                        {
                            "type": "score_update",
                            "scores": guess_result["scores"],
                        },
                        active_connections,
                    )

                    if guess_result["all_guessed"]:
                        end_result = await manager.end_round(room_id)

                        if end_result["game_over"]:
                            winner_info = end_result["winner"]
                            await manager.broadcast(
                                room_id,
                                {
                                    "message": f"game over, winner is {winner_info}"
                                },
                                active_connections,
                            )
                        else:
                            await manager.broadcast(
                                room_id,
                                {"message": "round ended, next round starting"},
                                active_connections,
                            )
                else:
                    await manager.broadcast(
                        room_id,
                        {
                            "type": "chat",
                            "username": username,
                            "text": msg["data"]["text"],
                        },
                        active_connections,
                    )

    except WebSocketDisconnect:
        active_connections.pop(username, None)
        await manager.remove_player(room_id, username)
        await manager.broadcast(room_id, {"message": f"player {username} left the game"}, active_connections)
                


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
