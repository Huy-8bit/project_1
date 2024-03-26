from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

import os
from dotenv import load_dotenv

load_dotenv()

ip = os.getenv("MONGO_IP")

MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_HOST = os.getenv("MONGO_IP")
MONGO_PORT = "27017"
MONGO_DATABASE = "cloud_backup"

DATABASE_URL = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"


client = AsyncIOMotorClient(DATABASE_URL)

# Define the MongoDB database
database = client["project1"]
