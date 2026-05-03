from pydantic import BaseModel
from typing import Optional,Dict,Any


MESSAGE_TYPES = [
    "join",
    "start",
    "draw",
    "chat",
    "correct_guess",
    "word",
    "word_hint",
    "score_update",
    "end_round"
]


class Message(BaseModel):
    type :str
    username:Optional[str] =None
    room_id :Optional[str]=None
    data: Optional[Dict[str, Any]] = None


# message validator
def validate_message(message:Message) -> Optional[Message]:
    if message.type not in MESSAGE_TYPES:
        return None
    
    if message.type == "draw":
        if isinstance(message.data,dict):
            if 'x' in message.data and 'y' in message.data:
                return message
            
            
    if message.type == "chat":
        if isinstance(message.data,dict):
            if "text" in message.data:
                return message
            

        
    if message.type == "join":
        if message.username is not None:
            if message.room_id is not None:
                return message

    
    if message.type == "start":
        if message.username is not None:
            if message.room_id is not None:
                if isinstance(message.data,dict):
                    if 'total_time' in message.data and 'word' in message.data:
                        return message
                    


    if message.type == "correct_guess":
        if message.username is not None:
            if isinstance(message.data,dict):
                if 'time_taken' in message.data and 'points' in message.data:
                    return message
        

    if message.type == "word":
        if message.username is not None:
            if isinstance(message.data,dict):
                if 'word' in message.data :
                    return message
        

    if message.type == "word_hint":
        if isinstance(message.data,dict):
                if 'hint' in message.data :
                    return message
        
        
    if message.type == "score_update":
        if isinstance(message.data, dict):
            if "scores" in message.data:
                return message

    if message.type == "end_round":
        if isinstance(message.data, dict):
            if "correct_word" in message.data and "scores" in message.data:
                return message
        
            
    return None