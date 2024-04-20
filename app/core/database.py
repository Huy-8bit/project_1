from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


# MONGO_INITDB_ROOT_USERNAME = ""
# MONGO_INITDB_ROOT_PASSWORD = ""
MONGO_HOST = "13.212.87.149"
MONGO_PORT = "27017"
MONGO_DATABASE = "cloud_backup"

# DATABASE_URL = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"

DATABASE_URL = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

# DATABASE_URL = "mongodb://54.254.58.42:27017"

client = AsyncIOMotorClient(DATABASE_URL)

# Define the MongoDB database
database = client["cloud_backup"]
