from app.api.auth.models import RegistrationRequest
import hashlib
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from app.core.database import database
from app.api.auth.models import EmailRequest
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.api.auth.models import PasswordResetRequest, PasswordResetModel, UserInfo
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
from app.api.auth.dependencies import get_current_user
from bson import ObjectId
import os
import uuid
import base64
import time

router = APIRouter()
user_collection = database.get_collection("users")

UPLOAD_DIRECTORY = "./data/avatars/"

sender_email = "webchat6969@gmail.com"
sender_password = "fxvn uepm wsqe pqmw"


def send_email(sender_email, sender_password, receiver_email, subject, message):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


def send_verification_email(email: str, code: str):
    sender_email = "webchat6969@gmail.com"
    sender_password = "fxvn uepm wsqe pqmw"
    receiver_email = email
    subject = "Webchat Verification Code"
    message = f"Your verification code is {code}"
    send_email(sender_email, sender_password, receiver_email, subject, message)


async def check_account(email):
    user = await user_collection.find_one({"email": email})
    if user:
        if "password" in user:
            return True
        else:
            return False
    else:
        return False


@router.post("/request-verification")
async def request_verification(email_request: EmailRequest):
    if await check_account(email_request.email):
        raise HTTPException(status_code=400, detail="Email has been registered")
    verification_code = str(random.randint(100000, 999999))
    temp_data = {
        "email": email_request.email,
        "verification_code": verification_code,
    }
    await user_collection.insert_one(temp_data)
    send_verification_email(email_request.email, verification_code)
    return {"message": "Verification email sent"}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
async def register(registration_request: RegistrationRequest):
    temp_data = await user_collection.find_one({"email": registration_request.email})
    if (
        not temp_data
        or temp_data["verification_code"] != registration_request.verification_code
    ):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    hashed_password = hash_password(registration_request.password)
    timestamp = time.time()
    unique_id = hashlib.sha256(
        f"{registration_request.email}{timestamp}".encode()
    ).hexdigest()
    user_document = {
        "_id": unique_id,
        "email": registration_request.email,
        "password": hashed_password,
    }
    result = await user_collection.insert_one(user_document)
    await user_collection.delete_one({"email": registration_request.email})
    return {"user_id": unique_id, "email": registration_request.email}


@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    user = await user_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(
            status_code=404, detail="User with this email does not exist"
        )
    verification_code = str(random.randint(100000, 999999))
    await user_collection.update_one(
        {"email": request.email}, {"$set": {"reset_code": verification_code}}
    )
    send_verification_email(request.email, verification_code)
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(reset_request: PasswordResetModel):
    user = await user_collection.find_one(
        {"email": reset_request.email, "reset_code": reset_request.verification_code}
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Invalid email or verification code"
        )
    else:
        await user_collection.update_one(
            {"email": reset_request.email}, {"$unset": {"reset_code": ""}}
        )
    hashed_password = hash_password(reset_request.new_password)
    await user_collection.update_one(
        {"email": reset_request.email}, {"$set": {"password": hashed_password}}
    )
    return {"message": "Password has been reset successfully"}
