from fastapi import FastAPI, HTTPException, Depends, APIRouter, Body
from typing import List
from app.core.database import database
from app.core.dependencies import get_current_active_user
from .models import FriendRequest, AcceptFriendRequest, FriendList
import json

router = APIRouter()


relationship_collection = database.get_collection("relationship")
user_collection = database.get_collection("usersInfo")


def clean_data(item, exclude_keys=["_id"]):
    if isinstance(item, list):
        return [clean_data(i, exclude_keys) for i in item]
    if isinstance(item, dict):
        return {
            k: clean_data(v, exclude_keys)
            for k, v in item.items()
            if k not in exclude_keys
        }
    return item


async def get_user_name(user_id):
    user = await user_collection.find_one({"id": user_id})
    return user["username"]


@router.post("/send_friend_request")
async def send_friend_request(
    request: FriendRequest, user_id: str = Depends(get_current_active_user)
):
    existing_request = await relationship_collection.find_one(
        {"user_id": request.to_user_id}
    )
    if not request.to_user_id in existing_request["requests"]:
        await relationship_collection.update_one(
            {"user_id": request.to_user_id},
            {"$push": {"requests": user_id["id"]}},
        )
    elif request.to_user_id in existing_request["requests"]:
        raise HTTPException(status_code=400, detail="Friend request already sent")

    return {"message": "Friend request sent successfully"}


@router.get("/get_relationships")
async def get_relationships(user_id: str = Depends(get_current_active_user)):
    user_relationship = await relationship_collection.find_one(
        {"user_id": user_id["id"]}
    )
    user_relationship = clean_data(user_relationship)

    result = {
        "friends": [],
        "requests": [],
    }

    for friend in user_relationship["friends"]:
        result["friends"].append(
            {"id": friend, "username": await get_user_name(friend)}
        )
    for request in user_relationship["requests"]:
        result["requests"].append(
            {"id": request, "username": await get_user_name(request)}
        )

    return json.loads(json.dumps(result))


@router.post("/accept_friend_request")
async def accept_friend_request(
    request: AcceptFriendRequest, user_id: str = Depends(get_current_active_user)
):
    existing_request = await relationship_collection.find_one(
        {"user_id": user_id["id"]}
    )
    if request.from_user_id in existing_request["requests"]:
        await relationship_collection.update_one(
            {"user_id": user_id["id"]},
            {"$push": {"friends": request.from_user_id}},
        )
        await relationship_collection.update_one(
            {"user_id": user_id["id"]},
            {"$pull": {"requests": request.from_user_id}},
        )
        await relationship_collection.update_one(
            {"user_id": request.from_user_id},
            {"$push": {"friends": user_id["id"]}},
        )
    else:
        raise HTTPException(status_code=400, detail="No friend request found")

    return {"message": "Friend request accepted"}
