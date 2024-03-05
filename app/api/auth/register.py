import hashlib
from fastapi import APIRouter, HTTPException, Form
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.database import database
import random

router = APIRouter()
user_collection = database.get_collection("usersInfo")


SENDER_EMAIL = "webchat6969@gmail.com"
SENDER_PASSWORD = "fxvn uepm wsqe pqmw"


def generate_user_id(username: str, email: str):
    # Concatenate username and email
    user_info = f"{username}{email}"
    # Hash the concatenated string using SHA256
    hashed_info = hashlib.sha256(user_info.encode()).hexdigest()
    return hashed_info


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
    receiver_email = email
    subject = "Webchat Verification Code"
    message = f"Your verification code is {code}"
    send_email(SENDER_EMAIL, SENDER_PASSWORD, receiver_email, subject, message)


async def check_account(email, username):
    userName = await user_collection.find_one({"username": username})
    userEmail = await user_collection.find_one({"email": email})

    # username or useremail already exists return True
    if userName or userEmail:
        return True
    else:
        return False


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
async def register_user(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
):
    if await check_account(email, username):
        raise HTTPException(status_code=400, detail="Account has been registered")

    user_id = generate_user_id(username, email)

    # delete verification code if it exists
    await user_collection.delete_one({"email": email})

    verification_code = str(random.randint(100000, 999999))
    user_data = {
        "id": user_id,
        "email": email,
        "username": username,
        "password": hash_password(password),
        "verification_code": verification_code,
    }
    await user_collection.insert_one(user_data)
    send_verification_email(email, verification_code)
    return {"message": "Verification email sent"}


@router.post("/verify-registration")
async def verify_registration(
    email: str = Form(...),
    verification_code: str = Form(...),
):
    user_data = await user_collection.find_one({"email": email})
    if not user_data or user_data["verification_code"] != verification_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    await user_collection.update_one(user_data, {"$unset": {"verification_code": ""}})
    return {"message": "Account has been verified"}


@router.post("/request-password-reset")
async def request_password_reset(email: str = Form(...)):
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=404, detail="User with this email does not exist"
        )
    verification_code = str(random.randint(100000, 999999))
    await user_collection.update_one(
        {"email": email}, {"$set": {"reset_code": verification_code}}
    )
    send_verification_email(email, verification_code)
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(
    email: str = Form(...),
    verification_code: str = Form(...),
    new_password: str = Form(...),
):
    user = await user_collection.find_one(
        {"email": email, "reset_code": verification_code}
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Invalid email or verification code"
        )
    else:
        await user_collection.update_one(
            {"email": email}, {"$unset": {"reset_code": ""}}
        )
    hashed_password = hash_password(new_password)
    await user_collection.update_one(
        {"email": email}, {"$set": {"password": hashed_password}}
    )
    return {"message": "Password has been reset successfully"}
