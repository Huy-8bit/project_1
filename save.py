# @router.post("/join_room")
# async def join_chatroom(
#     room_id: str = Form(...),
#     keyfile: UploadFile = File(...),
#     user_id: str = Depends(get_current_active_user),
# ):
#     if not check_user_exit(user_id):
#         raise HTTPException(status_code=404, detail="User not found")
#     room_data = await room_collection.find_one({"room_id": room_id})
#     if not room_data:
#         raise HTTPException(status_code=404, detail="Room not found")
#     uploaded_key = await keyfile.read()
#     uploaded_key_hash = hashlib.sha256(uploaded_key).hexdigest()
#     if uploaded_key_hash != room_data.get("key_hash"):
#         raise HTTPException(status_code=403, detail="Invalid key file")
#     file_room = (
#         await chat_collection.find({"room_id": room_id})
#         .sort("upload_time", -1)
#         .limit(100)
#         .to_list(length=100)
#     )
#     cleaned_files = clean_data(file_room)
#     return {"message": "Joined room successfully", "recent_files": cleaned_files}
