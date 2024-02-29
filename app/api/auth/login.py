from fastapi import APIRouter, HTTPException
from app.core.database import database
from app.api.auth.models import UserLogin, User
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
import hashlib
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()

user_collection = database.get_collection("usersInfo")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


async def check_user_login(email, password):
    user = await user_collection.find_one({"email": email})
    if user and user["password"] == hash_password(password):
        return True
    return False


@router.post("/login")
async def login(user: UserLogin):
    if not await check_user_login(user.email, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    user = await user_collection.find_one({"email": user.email})
    if user:
        user_id = user["_id"]
    else:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token({"user_id": user_id})
    return {
        "access_token": access_token,
        "user_id": user_id,
    }
