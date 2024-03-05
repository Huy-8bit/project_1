from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

DATABASE_URL = "mongodb://localhost:27017"

client = AsyncIOMotorClient(DATABASE_URL)

# Define the MongoDB database
database = client["project1"]
