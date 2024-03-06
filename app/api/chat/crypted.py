import asyncio
from cryptography.fernet import Fernet
import os


def ensure_path_exists(save_path):
    os.makedirs(save_path, exist_ok=True)


async def saveFile(save_path, data):
    with open(save_path, "wb") as buffer:
        buffer.write(data)


def generate_and_save_key(key_file_path):
    key = Fernet.generate_key()
    with open(key_file_path, "wb") as filekey:
        filekey.write(key)
    return key


def load_key(key_file_path):
    with open(key_file_path, "rb") as filekey:
        key = filekey.read()
    return key


def encrypt_file(data, key):
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)
    return encrypted


def decrypt_file(data, key):
    fernet = Fernet(key)
    decrypted = fernet.decrypt(data)
    return decrypted
