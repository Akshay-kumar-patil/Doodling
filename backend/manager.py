import asyncio
from typing import Dict, List
import random

WORD_DATABASE = [
    "apple", "banana", "car", "dog", "elephant",
    "flower", "guitar", "house", "ice cream", "jacket",
    "kite", "laptop", "monkey", "nose", "orange",
    "piano", "queen", "rainbow", "snake", "tree",
    "umbrella", "violin", "whale", "xylophone", "zebra",
    "bicycle", "candle", "dragon", "eagle", "forest",
    "globe", "hammer", "island", "jungle", "knight",
    "lemon", "mountain", "nurse", "ocean", "pencil",
    "rocket", "stadium", "tiger", "universe", "volcano",
    "window", "yacht", "castle", "diamond","fish","bed", 
    "ant", "bat", "bee", "butterfly", "cat", "chicken", 
    "cow", "crab", "dinosaur", "dolphin", "duck", "fox", "frog",
    "giraffe", "hippo", "horse", "jellyfish", "kangaroo", "lion", 
    "lizard", "mouse", "octopus", "owl", "panda", "penguin", "pig", 
    "rabbit", "shark", "sheep", "spider", "starfish", "turtle", 
    "unicorn", "worm", "burger", "cake", "carrot", "cheese", 
    "cherry", "cookie", "cupcake", "donut", "egg", "fries", "grapes", 
    "hot dog", "lollipop", "milk", "mushroom", "pear", "pizza", 
    "popcorn", "sandwich", "strawberry", "taco", "watermelon", 
    "backpack", "ball", "balloon", "blanket", "book", 
    "bottle", "bowl", "box", "broom", "chair", "clock", "computer", "cup", 
    "door", "fork", "glasses", "hat", "key", "lamp", "mailbox", 
    "mirror", "phone", "pillow", "plate", "ring", "scissors", "shirt", "shoes", "soap", 
    "socks", "spoon", "table", "toothbrush", "towel", "watch", "beach", "cloud", 
    "farm", "leaf", "moon", "rain", "snowman", "sun"

]
 

rooms: Dict[str, dict] = {}

async def create_room(room_id,host_username) -> dict :
    if room_id in rooms:
        return {"success": False, "error": "room already exists"}
    
    rooms[room_id]={
        "players":[],
        "host":host_username,
        "scores":{},
        "drawer":None,
        "word":None,
        "round_active":False,
        "start_time":None,
        "total_time":None,
        "correct_guessers":[],
        "visited_words":[],
        "word_choices":[],
        "drawer_index":0,
        "total_rounds": None,
        "current_round": 0, 
        "timer_task":None,
    }

    return {"success":True,"room_id":room_id}

#  other palyer can join
async def join_room(room_id,username) -> dict:
    if room_id not in rooms:
        return {"success":False,"error": "room not found"}
    
    room=rooms[room_id]

    if username in room["players"]:
        return {"success":False,"error": "username already taken"}
    
    room["players"].append(username)
    room["scores"][username]=0

    return {"success": True, "username": username, "room_id": room_id}

# remove player or allow player to exit

async def remove_player(room_id,username) ->dict :
    if room_id not in rooms:
        return {"success":False,"error": "room not found"}
    
    room=rooms[room_id]
    
    if username in room["players"]:
        room["players"].remove(username)
        del room["scores"][username]

    if len(room["players"])==0:
        del rooms[room_id]
        return {"success": True, "message": "room deleted, no players left"}
    
    if username == room["drawer"] and room["round_active"]:
        await end_round(room_id)

    return {"success": True}

# get the current time of the room
async def get_room_state(room_id) ->dict:
    if room_id not in rooms:
        return {"success": False, "error": "room not found"}
    
    room=rooms[room_id]

    time_remaining=0
    if room["round_active"] and room["start_time"] is not None:
        time_passed=asyncio.get_event_loop().time()-room["start_time"]
        time_remaining=max(0,room["total_time"]-time_passed)

    return {
        "success": True,
        "players": room["players"],
        "scores": room["scores"],
        "drawer": room["drawer"],
        "round_active": room["round_active"],
        "time_remaining": round(time_remaining),
    }

#  choose word
async def get_word_choices(room_id) -> List[str]:
    if room_id not in rooms:
        return []

    room=rooms[room_id]

    available_words = [
        word for word in WORD_DATABASE
        if word not in room["visited_words"]
    ]

    if len(available_words)<3:
        room["visited_words"] =[]
        available_words =WORD_DATABASE.copy()

    choices=random.sample(available_words,3)
    room["word_choices"]=choices

    return choices

# select one of these three words
async def select_word(room_id , choosen_word)->dict:
    if room_id not in rooms:
        return {"success": False, "error": "room not found"}

    room=rooms[room_id]

    if choosen_word not in room["word_choices"]:
        return {"success": False, "error": "invalid word choice"}
    
    room["word"]=choosen_word
    room["visited_words"].append(choosen_word)
    room["word_choices"] = []

    return {"success": True, "word": choosen_word}

async def start_round(room_id,total_time,total_rounds) ->dict:
    if room_id not in rooms:
        return {"success": False, "error": "room not found"}
    
    room=rooms[room_id]

    if len(room["players"])<2:
        return {"success":False, "error":"need at least 2 players"}

    if room["round_active"]:
        return {"success": False, "error": "round already active"}
    
    room["drawer"]=room["players"][room["drawer_index"]]

    room["total_time"]=total_time
    room["start_time"]=asyncio.get_event_loop().time()
    room["round_active"]=True
    room["correct_guessers"]=[]

    room["total_rounds"]=total_rounds
    room["current_round"] += 1

    word_choices=await get_word_choices(room_id)
    
    room["timer_task"]=asyncio.create_task(countdown_timer(room_id,total_time))

    return {
        "success":True,
        "drawer":room["drawer"],
        "word_choices":word_choices,
        "total_time":total_time,
    }

async def countdown_timer(room_id, total_time):
    await asyncio.sleep(total_time)

    if room_id in rooms and rooms[room_id]["round_active"]:
        await end_round(room_id)

async def end_round(room_id) ->dict:
    if room_id not in rooms:
        return {"success": False, "error": "room not found"}
    
    room=rooms[room_id]

    room["round_active"] =False

    if room["timer_task"] is not None:
        room["timer_task"].cancel()
        room["timer_task"]=None

    correct_word=room["word"]
    room["word"]=None
    room["word_choices"] = []
    room["correct_guessers"] = []
    
    room["drawer_index"]=(room["drawer_index"] +1 ) % len(room["players"])

    if room["current_round"]==room["total_rounds"]:
        winner=await announce_winner(room_id)
        return {
            "success":True,
            "correct_word":correct_word,
            "scores":room["scores"],
            "game_over": True,  
            "winner": winner,
        }

    return {
        "success":True,
        "correct_word":correct_word,
        "scores":room["scores"],
        "game_over": False,
    }

async def announce_winner(room_id) ->dict:
    room=rooms[room_id]

    winner= max(room["scores"], key=lambda player: room["scores"][player])
    highest_score=room["scores"][winner]

    tied_players=[
        player for player,scores in room["scores"].items() if scores == highest_score
    ]

    if len(tied_players) >1:
        return {
            "tie":True,
            "winners":tied_players,
            "scores":highest_score,
            "all_scores": room["scores"],  
        }
    
    return {
        "tie": False,
        "winner": winner,
        "score": highest_score,
        "all_scores": room["scores"],  
    }

#  tells the user about the length of the word
def get_word_hint(word: str) -> str:
    return " ".join("_" for letter in word)

# guess the word 
async def handle_guess(room_id,username,guessed_text,active_connections) ->dict:
    if room_id not in rooms:
        return {"success": False, "error": "room not found"}
    
    room=rooms[room_id]

    if not room["round_active"]:
        return {"success":False , "error":"round is not active"}
    
    if username == room["drawer"]:
        return {
            "success": True,
            "correct": False,
            "username": username,
            "text": guessed_text,
        }
    
    if username in room["correct_guessers"]:
        return {"success": False, "error": "already guessed correctly"}

    if room["word"] is None:
        return {"success": False, "error": "word not selected yet"}
    
    if guessed_text.lower().strip() == room["word"].lower().strip():
        time_passed=asyncio.get_event_loop().time() -room["start_time"]
        time_remaining=room["total_time"]-time_passed

        # giving points based on time
        # guessed in first half -> 10 points
        #  guessed in second half ->5 , 6, or 7 points

        if time_passed<=room["total_time"]/2:
            points=10
        else:
            ratio=time_remaining/room["total_time"]
            points=5+round(ratio *2)

        
        room["scores"][username]+=points
        room["correct_guessers"].append(username)

        # check if all guessers have guesses correctly
        guessers = [p for p in room["players"] if p != room["drawer"]]
        all_guessed= all(p in room["correct_guessers"] for p in guessers)

        return {
            "success": True,
            "correct": True,
            "username": username,
            "points": points,
            "scores": room["scores"],
            "all_guessed": all_guessed,
        }
    
    else:
        return {
            "success": True,
            "correct": False,
            "username": username,
            "text": guessed_text,
        }
    
# send message to all player in that room
async def broadcast(room_id,message,active_connection):
    if room_id not in rooms:
        return

    room=rooms[room_id]
    for username in room["players"]:
        if username in active_connection:
            websocket=active_connection[username]
            try:
                await websocket.send_json(message)
            except Exception:
                active_connection.pop(username, None)


# send message to one specific player only
async def send_to_one(username, message, active_connection):
    if username in active_connection:
        websocket= active_connection[username]
        try:
            await websocket.send_json(message)
        except Exception:
            active_connection.pop(username, None)

# send message to everyone except drawer
async def broadcast_except(room_id, exclude_username, message, active_connections):
    if room_id not in rooms:
        return

    room = rooms[room_id]
    for username in room["players"]:
        if username != exclude_username:        
            if username in active_connections:
                websocket = active_connections[username]
                try:
                    await websocket.send_json(message)
                except Exception:
                    active_connections.pop(username, None)
