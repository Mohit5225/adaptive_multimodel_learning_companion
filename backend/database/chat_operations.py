"""
Chat Database Operations
MongoDB CRUD for Chats and ChatMessages — fully indexed per user.
"""
from typing import List, Optional, Dict
from datetime import datetime, timezone
from bson import ObjectId
from database.db import db


# ═════════════════════════════════════════════════════════════════════════════
# COLLECTION REFERENCES
# ═════════════════════════════════════════════════════════════════════════════
chats_collection = db.chats
messages_collection = db.chat_messages


# ═════════════════════════════════════════════════════════════════════════════
# INDEX CREATION (called once at startup)
# ═════════════════════════════════════════════════════════════════════════════
async def ensure_chat_indexes():
    """Create indexes for efficient per-user queries. Idempotent."""
    print("📇 [DB] Creating chat indexes...")

    # Chats: fast lookup by user, sorted by recent
    await chats_collection.create_index(
        [("user_id", 1), ("created_at", -1)],
        name="idx_chats_user_date",
    )
    await chats_collection.create_index("user_id", name="idx_chats_user")

    # Messages: fast lookup by chat_id + chronological order
    await messages_collection.create_index(
        [("chat_id", 1), ("created_at", 1)],
        name="idx_messages_chat_date",
    )
    # Messages: per-user index for cross-chat operations
    await messages_collection.create_index(
        [("user_id", 1), ("created_at", -1)],
        name="idx_messages_user_date",
    )

    print("✅ [DB] Chat indexes ready.")


# ═════════════════════════════════════════════════════════════════════════════
# CHAT CRUD
# ═════════════════════════════════════════════════════════════════════════════

async def create_chat(user_id: str, title: str = None) -> dict:
    """Create a new chat session for user."""
    chat_doc = {
        "user_id": user_id,
        "title": title or "New Chat",
        "total_messages": 0,
        "total_videos_generated": 0,
        "total_text_responses": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "archived": False,
    }
    result = await chats_collection.insert_one(chat_doc)
    chat_doc["_id"] = result.inserted_id
    print(f"✅ [DB] Chat created: {result.inserted_id} for user {user_id}")
    return serialize_chat(chat_doc)


async def get_user_chats(user_id: str, limit: int = 50) -> List[dict]:
    """Get all non-archived chats for a user, most recent first."""
    cursor = chats_collection.find(
        {"user_id": user_id, "archived": False}
    ).sort("updated_at", -1).limit(limit)
    chats = await cursor.to_list(length=limit)
    return [serialize_chat(c) for c in chats]


async def get_chat_by_id(chat_id: str, user_id: str) -> Optional[dict]:
    """Get a specific chat, ensuring it belongs to user."""
    try:
        chat = await chats_collection.find_one({
            "_id": ObjectId(chat_id),
            "user_id": user_id,
        })
        return serialize_chat(chat) if chat else None
    except Exception:
        return None


async def update_chat_title(chat_id: str, user_id: str, title: str) -> bool:
    """Update chat title."""
    result = await chats_collection.update_one(
        {"_id": ObjectId(chat_id), "user_id": user_id},
        {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
    )
    return result.modified_count > 0


async def archive_chat(chat_id: str, user_id: str) -> bool:
    """Soft-delete a chat."""
    result = await chats_collection.update_one(
        {"_id": ObjectId(chat_id), "user_id": user_id},
        {"$set": {"archived": True, "updated_at": datetime.now(timezone.utc)}},
    )
    return result.modified_count > 0


# ═════════════════════════════════════════════════════════════════════════════
# MESSAGE CRUD
# ═════════════════════════════════════════════════════════════════════════════

async def save_message(
    chat_id: str,
    user_id: str,
    user_message: str,
    classification: dict,
    routed_to: str,
    system_response: str = None,
    video_url: str = None,
) -> dict:
    """
    Save a complete message pair (user input + system response) to DB.
    Also increments chat counters.
    """
    print(f"   💾 [DB] Saving message to chat {chat_id} (routed_to: {routed_to})")

    msg_doc = {
        "chat_id": chat_id,
        "user_id": user_id,
        "user_message": user_message,
        "classification": classification,
        "routed_to": routed_to,
        "system_response": system_response,
        "video_url": video_url,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }

    result = await messages_collection.insert_one(msg_doc)
    msg_doc["_id"] = result.inserted_id
    print(f"   💾 [DB] Message saved with ID: {result.inserted_id}")

    # Update chat counters
    inc_fields = {"total_messages": 1}
    if routed_to == "video_generation":
        inc_fields["total_videos_generated"] = 1
    else:
        inc_fields["total_text_responses"] = 1

    await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {
            "$inc": inc_fields,
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )

    print(f"✅ [DB] Message saved: {result.inserted_id} in chat {chat_id}")
    return serialize_message(msg_doc)


async def get_chat_messages(
    chat_id: str,
    user_id: str,
    limit: int = 50,
    before_id: str = None,
) -> List[dict]:
    """
    Get messages for a chat, ordered chronologically (oldest first).
    Supports cursor-based pagination via before_id.
    """
    query = {"chat_id": chat_id, "user_id": user_id}
    if before_id:
        try:
            query["_id"] = {"$lt": ObjectId(before_id)}
        except Exception:
            pass

    cursor = messages_collection.find(query).sort("created_at", 1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return [serialize_message(m) for m in messages]


async def get_recent_history(chat_id: str, user_id: str, limit: int = 20) -> List[dict]:
    """
    Get last N messages for context window (used by Gemini text generation).
    Returns in chronological order (oldest first).
    """
    print(f"   📚 [DB] Fetching recent history for chat {chat_id} (limit: {limit})")

    cursor = (
        messages_collection.find({"chat_id": chat_id, "user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    messages = await cursor.to_list(length=limit)
    messages.reverse()  # Chronological order

    print(f"   📚 [DB] Retrieved {len(messages)} messages for context")

    # Convert to simple format for Gemini context
    history = []
    for msg in messages:
        history.append({"role": "user", "content": msg["user_message"]})
        if msg.get("system_response"):
            history.append({"role": "ai", "content": msg["system_response"]})

    print(f"📚 [DB] Fetched {len(history)} history entries for chat {chat_id}")
    return history


# ═════════════════════════════════════════════════════════════════════════════
# AUTO-TITLE GENERATION
# ═════════════════════════════════════════════════════════════════════════════

async def auto_title_chat(chat_id: str, user_id: str, first_message: str):
    """Auto-generate chat title from first message (truncated)."""
    title = first_message[:60].strip()
    if len(first_message) > 60:
        title += "..."
    await update_chat_title(chat_id, user_id, title)


# ═════════════════════════════════════════════════════════════════════════════
# SERIALIZERS
# ═════════════════════════════════════════════════════════════════════════════

def serialize_chat(chat: dict) -> dict:
    """Convert MongoDB chat document to JSON-safe dict."""
    return {
        "id": str(chat["_id"]),
        "user_id": chat.get("user_id"),
        "title": chat.get("title", "New Chat"),
        "total_messages": chat.get("total_messages", 0),
        "total_videos_generated": chat.get("total_videos_generated", 0),
        "total_text_responses": chat.get("total_text_responses", 0),
        "created_at": chat.get("created_at").isoformat() if chat.get("created_at") else None,
        "updated_at": chat.get("updated_at").isoformat() if chat.get("updated_at") else None,
        "archived": chat.get("archived", False),
    }


def serialize_message(msg: dict) -> dict:
    """Convert MongoDB message document to JSON-safe dict."""
    return {
        "id": str(msg["_id"]),
        "chat_id": msg.get("chat_id"),
        "user_id": msg.get("user_id"),
        "user_message": msg.get("user_message"),
        "classification": msg.get("classification"),
        "routed_to": msg.get("routed_to"),
        "system_response": msg.get("system_response"),
        "video_url": msg.get("video_url"),
        "created_at": msg.get("created_at").isoformat() if msg.get("created_at") else None,
        "updated_at": msg.get("updated_at").isoformat() if msg.get("updated_at") else None,
    }
