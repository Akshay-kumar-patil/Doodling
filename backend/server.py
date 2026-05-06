import asyncio
from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from typing import Dict,List
import uvicorn
import manager
from models import message

app=FastAPI()

# it stores all the active connection of websocket
# { "username": websocket_object } 
active_connections:dict[str,WebSocket] ={}

# when host create room
@app.post("/Host/create-room/{room_id}") 
async def host_create_room(room_id,username,total_rounds,total_time) ->dict :
    connect=await manager.create_room(room_id=room_id,host_username=username)
    if connect["success"] == True:
        print("room_created")
        return connect
    else:
        return {"success": False, "error": "room already exists"}


@app.websocket("/ws/new-join/{room_id}/{username}")
async def player_connection(websocket:WebSocket,username:str,room_id):
    await websocket.accept()
    active_connections[username]=websocket
    print(f"Player {username} has been added")
    join = await manager.join_room(room_id=room_id,username=username)

    if join["success"] == True:
        print(f"player {username} joined")
        return join
    else:
        return join

@app.websocket("/ws/{room_id}/{username}")
async def send_message(websocket: WebSocket, room_id: str, username: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()

        msg=message.validate_message(data)
        if msg == None:
            print("please send us a valid message")
            return None
        
        if msg.type == "start":
            start = await manager.start_round(room_id=msg.room_id,total_time=msg.data["total_time"],total_rounds=msg.data["total_rounds"])

            if start["success"] == False:
                print("error in create room")
                return start
            
            manager.send_to_one(start["drawer"],{start["word_choices"]})
            await manager.broadcast(room_id,message={type: "start", "drawer":start["drawer"]})
            

        if msg.type == "word_selected":
            select = await manager.select_word(room_id=msg.room_id,choosen_word=msg.data["select_word"])
            
            if select["success"] == False:
                return select
            
            manager.send_to_one(username=msg.username,message=select["word"])
            manager.broadcast(room_id=room_id,active_connection=active_connections,message=manager.get_word_hint(select["word"]))


        if msg.type == "draw":
            #  ****** i dont know do i broadcast data to every one ******
            manager.broadcast_except(room_id=room_id,username=msg.username,active_connections=active_connections, message=msg.data)

            
        if msg.type == "chat":
            chat= await manager.handle_guess(room_id=room_id, username=msg.data["username"],guessesd_text=msg.data["guessed_text"])

            if chat["success"] == True:
                manager.broadcast(room_id=room_id,active_connection=active_connections,message="{msg.username} guessed correctly ")

                if chat["all_guessed"]:
                    manager.broadcast
            


if __name__ == "__main__":
    asyncio.run(main())