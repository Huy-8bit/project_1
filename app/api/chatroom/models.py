from pydantic import BaseModel


class ChatRoom(BaseModel):
    id: str
    key_password_hash: str
