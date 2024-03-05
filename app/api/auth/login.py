from fastapi import APIRouter, HTTPException, Form
from app.core.database import database
from app.api.auth.models import UserLogin, User
from app.core.accesstoken import create_access_token
import hashlib
from fastapi.middleware.cors import CORSMiddleware


router = APIRouter()

user_collection = database.get_collection("usersInfo")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


async def check_user_login(username: str, password: str) -> bool:
    user = await user_collection.find_one(
        {"username": username, "password": hash_password(password)}
    )
    return user is not None


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if not await check_user_login(username, password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = await user_collection.find_one({"username": username})
    access_token = create_access_token({"id": user["id"]})
    return {
        "access_token": access_token,
        "id": user["id"],
    }
