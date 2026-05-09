from pydantic import BaseModel
from typing import Optional,Dict,Any


MESSAGE_TYPES = [
    "start",
    "word_selected",
    "draw",
    "chat",
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

    if message.type == "chat":
        if isinstance(message.data,dict):
            if "text" in message.data:
                return message

    if message.type == "start":
        if isinstance(message.data,dict):
            if 'total_time' in message.data and 'total_rounds' in message.data:
                return message

    if message.type == "word_selected":
        if isinstance(message.data,dict):
            if 'select_word' in message.data:
                return message

        
    if message.type == "draw":
        if isinstance(message.data,dict):
            if 'x' in message.data and 'y' in message.data and 'color' in message.data and 'size' in message.data:
                return message

    return None
