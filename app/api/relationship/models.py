from pydantic import BaseModel
from typing import List, Dict


class FriendRequest(BaseModel):
    to_user_id: str


class AcceptFriendRequest(BaseModel):
    from_user_id: str


class FriendList(BaseModel):
    user_id: str
    friends: List[str]
    requests: List[str]
