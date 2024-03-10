from pydantic import BaseModel
from typing import List, Dict


class ChatRoom(BaseModel):
    name: str
    # password: str
