from fastapi import APIRouter, HTTPException, Depends, Body, Form, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Dict
import hashlib
import time
import random
from app.core.dependencies import get_current_active_user
from app.core.accesstoken import verify_access_token, check_user_exit
from app.core.database import database
from app.api.chat.models import ChatRoom
import os
from pathlib import Path

router = APIRouter()

room_collection = database.get_collection("chatrooms")

chat_collection = database.get_collection("chats")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def crate_rooom_id(roomName: str) -> str:
    room_id = f"{roomName}{time.time()}{random.randint(1, 1000)}"
    return hashlib.sha256(room_id.encode()).hexdigest()


@router.post("/create_room")
async def create_chatroom(
    room: ChatRoom = Body(...), user_id: str = Depends(get_current_active_user)
):
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    room_id = crate_rooom_id(room.name)
    room_data = room.dict()
    room_data["room_id"] = room_id
    room_data["created_at"] = time.time()
    room_data["key_hash"] = hash_password(room.password)
    room_data["created_by"] = user_id["id"]
    del room_data["password"]
    room_collection.insert_one(room_data)
    return {"message": "Room created successfully", "room_id": room_id}


@router.get("/test")
async def test():
    return {"message": "Hello Project 1!"}


@router.post("/find_room")
async def find_room(room_name: str = Form(...)):
    cursor = room_collection.find({"name": room_name})
    rooms = await cursor.to_list(length=100)

    if rooms:
        result = [{"name": room["name"], "room_id": room["room_id"]} for room in rooms]
        return result
    else:
        return {"message": "Room not found"}


@router.post("/upload")
async def upload_file(
    user_id: str = Depends(get_current_active_user),
    room_id: str = Form(...),
    file: UploadFile = File(...),
):
    save_path = "./data/uploaded_files"
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    room = await room_collection.find_one({"room_id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    Path(save_path).mkdir(parents=True, exist_ok=True)

    file_path = os.path.join(save_path, file.filename)

    with open(file_path, "wb") as buffer:
        while data := await file.read(1024):
            buffer.write(data)
    return {"message": "File uploaded successfully", "file_path": file_path}
