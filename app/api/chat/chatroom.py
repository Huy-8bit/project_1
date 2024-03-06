from fastapi import (
    BackgroundTasks,
    Depends,
    Form,
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Body,
)
from fastapi.responses import FileResponse
import os
import shutil
from fastapi.responses import FileResponse
from typing import List, Dict
import hashlib
import time
import base64
import random
from app.core.dependencies import get_current_active_user
from app.core.accesstoken import check_user_exit
from app.core.database import database
from app.api.chat.models import ChatRoom
from cryptography.fernet import Fernet
from pathlib import Path
from app.api.chat.crypted import (
    saveFile,
    ensure_path_exists,
    generate_and_save_key,
    load_key,
    encrypt_file,
    decrypt_file,
)

router = APIRouter()

room_collection = database.get_collection("chatrooms")
chat_collection = database.get_collection("chats")


def generate_file_name(original_name: str) -> str:
    name_seed = f"{original_name}{time.time()}"
    hashed_name = hashlib.sha256(name_seed.encode()).hexdigest()
    return hashed_name


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def crate_rooom_id(roomName: str) -> str:
    room_id = f"{roomName}{time.time()}{random.randint(1, 1000)}"
    return hashlib.sha256(room_id.encode()).hexdigest()


@router.post("/find_room")
async def find_room(room_name: str = Form(...)):
    cursor = room_collection.find({"name": room_name})
    rooms = await cursor.to_list(length=100)

    if rooms:
        result = [{"name": room["name"], "room_id": room["room_id"]} for room in rooms]
        return result
    else:
        return {"message": "Room not found"}


@router.post("/create_room")
async def create_chatroom(
    room: ChatRoom = Body(...), user_id: str = Depends(get_current_active_user)
):
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    room_id = crate_rooom_id(room.name)
    password_hash = hash_password(room.password)

    key_file_name = f"{password_hash}.key"
    key_file_path = os.path.join("data", "key", key_file_name)
    # key_file_path = f"./data/key/{key_file_name}"
    print(key_file_path)

    ensure_path_exists(os.path.dirname(key_file_path))

    key = generate_and_save_key(key_file_path)

    room_data = room.dict()
    room_data["room_id"] = room_id
    room_data["created_at"] = time.time()
    room_data["key_file"] = key_file_name
    room_data["created_by"] = user_id["id"]
    del room_data["password"]
    room_collection.insert_one(room_data)

    return {
        "message": "Room created successfully",
        "room_id": room_id,
        "key_file": key_file_name,
    }


@router.post("/upload")
async def upload_file_encrypted(
    user_id: str = Depends(get_current_active_user),
    room_id: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
):

    room_data = room_collection.find_one({"room_id": room_id})
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    password_hash = hash_password(password)
    key_file_name = f"{password_hash}.key"
    key_file_path = os.path.join("data", "key", key_file_name)
    # key_file_path = f"./data/key/{key_file_name}"
    if not os.path.exists(key_file_path):
        raise HTTPException(status_code=404, detail="Encryption key not found")

    key = load_key(key_file_path)

    file_data = await file.read()

    encrypted_data = encrypt_file(file_data, key)

    new_file_name = generate_file_name(file.filename) + ".encrypted"
    save_path = os.path.join("data", "encrypted_files", new_file_name)

    await saveFile(save_path, encrypted_data)

    chat_data = {
        "user_id": user_id["id"],
        "room_id": room_id,
        "file_name": file.filename,
        "encrypted_file_name": new_file_name,
        "file_path": save_path,
        "key_name": key_file_name,
        "upload_time": time.time(),
    }
    chat_collection.insert_one(chat_data)

    return {
        "message": "File uploaded and encrypted successfully",
        "encrypted_file_name": new_file_name,
        "file_name": file.filename,
    }


def decrypt_file(encrypted_data: bytes, key: bytes) -> bytes:
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data


@router.post("/download")
async def download_file_encrypted(
    user_id: str = Depends(get_current_active_user),
    room_id: str = Form(...),
    password: str = Form(...),
    file_id: str = Form(...),
):

    room_data = await room_collection.find_one({"room_id": room_id})
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    key_file_name = f"{password_hash}.key"
    key_file_path = os.path.join("data", "key", key_file_name)
    # key_file_path = f"./data/key/{key_file_name}"

    if not os.path.exists(key_file_path):
        raise HTTPException(status_code=404, detail="Encryption key not found")

    key = load_key(key_file_path)

    chat_data = await chat_collection.find_one({"encrypted_file_name": file_id})

    if not chat_data:
        raise HTTPException(status_code=404, detail="File not found")

    encrypted_file_path = chat_data["file_path"]

    with open(encrypted_file_path, "rb") as file:
        encrypted_data = file.read()

    decrypted_data = decrypt_file(encrypted_data, key)

    temp_file_path = f"temp/{chat_data['file_name']}"
    ensure_path_exists(os.path.dirname(temp_file_path))
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(decrypted_data)

    response = FileResponse(
        path=temp_file_path,
        filename=chat_data["file_name"],
        media_type="application/octet-stream",
    )

    # # save file to temp folder
    # saveFile(temp_file_path, decrypted_data)

    return response
