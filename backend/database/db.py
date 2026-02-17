import motor.motor_asyncio
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

# Create the Async Client
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL, tls=True, tlsCAFile=certifi.where())

# Point to your specific DB
db = client.hackathon_db

# Helper to fix the "_id" object madness
def user_helper(user) -> dict:
    
    return {
        "id": str(user["_id"]),
        "clerk_id": user["clerk_id"],
        "email": user["email"],
        "role": user.get("role", "student"),
    }