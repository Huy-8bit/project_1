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
import io
from fastapi.responses import StreamingResponse
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

from bson import ObjectId


router = APIRouter()


def clean_data(item, exclude_keys=["_id", "room_id", "file_path", "uploaded_by"]):
    if isinstance(item, ObjectId):
        return str(item)
    if isinstance(item, list):
        return [clean_data(i, exclude_keys) for i in item]
    if isinstance(item, dict):
        return {
            k: clean_data(v, exclude_keys)
            for k, v in item.items()
            if k not in exclude_keys
        }
    return item


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


@router.post("/create_room", response_class=FileResponse)
async def create_chatroom(
    room: ChatRoom = Body(...), user_id: str = Depends(get_current_active_user)
):
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    room_id = crate_rooom_id(room.name)

    key = Fernet.generate_key()
    key_hash = hashlib.sha256(key).hexdigest()
    key_stream = io.BytesIO(key)
    key_stream.seek(0)

    file_name = f"{room_id}.key"

    room_data = room.dict()
    room_data["room_id"] = room_id
    room_data["created_at"] = time.time()
    room_data["key_hash"] = key_hash
    room_data["created_by"] = user_id["id"]
    # del room_data["password"]
    room_collection.insert_one(room_data)

    return StreamingResponse(
        key_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}",
            "room_id": room_id,
        },
    )


@router.post("/join_room")
async def join_chatroom(
    room_id: str = Form(...),
    keyfile: UploadFile = File(...),
    user_id: str = Depends(get_current_active_user),
):

    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    room_data = await room_collection.find_one({"room_id": room_id})

    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    uploaded_key = await keyfile.read()
    uploaded_key_hash = hashlib.sha256(uploaded_key).hexdigest()
    if uploaded_key_hash != room_data.get("key_hash"):
        raise HTTPException(status_code=403, detail="Invalid key file")

    file_room = (
        await chat_collection.find({"room_id": room_id})
        .sort("upload_time", -1)
        .limit(100)
        .to_list(length=100)
    )

    cleaned_files = clean_data(file_room)
    return {"message": "Joined room successfully", "recent_files": cleaned_files}


@router.post("/upload")
async def upload_file_encrypted(
    room_id: str = Form(...),
    keyfile: UploadFile = File(...),
    user_id: str = Depends(get_current_active_user),
    file: UploadFile = File(...),
):

    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    room_data = await room_collection.find_one({"room_id": room_id})
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    uploaded_key = await keyfile.read()
    uploaded_key_hash = hashlib.sha256(uploaded_key).hexdigest()
    if uploaded_key_hash != room_data.get("key_hash"):
        raise HTTPException(status_code=403, detail="Invalid key file")

    # encrypt file
    key = Fernet(uploaded_key)
    file_data = await file.read()
    encrypted_data = key.encrypt(file_data)

    file_name = file.filename
    file_id = generate_file_name(file_name)

    await saveFile(f"data/encrypted_files/{file_id}", encrypted_data)

    chat_data = {
        "room_id": room_id,
        "file_name": file_name,
        "file_id": file_id,
        "file_path": f"data/encrypted_files/{file_id}",
        "upload_time": time.time(),
        "uploaded_by": user_id["id"],
    }
    chat_collection.insert_one(chat_data)

    return {
        "message": "File uploaded successfully",
        "file_id": file_id,
        "file_name": file_name,
    }


def decrypt_file(encrypted_data: bytes, key: bytes) -> bytes:
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data


@router.post("/download")
async def download_file_encrypted(
    room_id: str = Form(...),
    keyfile: UploadFile = File(...),
    user_id: str = Depends(get_current_active_user),
    file_id: str = Form(...),
):
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    room_data = await room_collection.find_one({"room_id": room_id})
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    uploaded_key = await keyfile.read()
    uploaded_key_hash = hashlib.sha256(uploaded_key).hexdigest()
    if uploaded_key_hash != room_data.get("key_hash"):
        raise HTTPException(status_code=403, detail="Invalid key file")

    file_data = await chat_collection.find_one({"file_id": file_id})
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(file_data["file_path"], "rb") as file:
            encrypted_data = file.read()
    except IOError:
        raise HTTPException(status_code=500, detail="Error reading file")

    key = Fernet(uploaded_key)
    decrypted_data = key.decrypt(encrypted_data)
    file_name = file_data["file_name"]

    return StreamingResponse(
        io.BytesIO(decrypted_data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )
