from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from svix.webhooks import Webhook, WebhookVerificationError
import os
import shutil
from typing import Optional, List
from pydantic import BaseModel
import datetime
from pathlib import Path
from dotenv import load_dotenv
import logging
import sys

# ═════════════════════════════════════════════════════════════════════════════
# CRITICAL: Disable Python output buffering so print() shows in real-time
# ═════════════════════════════════════════════════════════════════════════════
# This is the #1 reason logs don't appear when running under uvicorn
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
os.environ["PYTHONUNBUFFERED"] = "1"

# Override builtin print to always flush (ensures logs appear immediately)
import builtins
_original_print = builtins.print
def _flushed_print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    _original_print(*args, **kwargs)
builtins.print = _flushed_print

# ═════════════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION — Force all logs to stdout, unbuffered
# ═════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
    force=True,  # Override any pre-existing logging config (e.g. uvicorn's)
)
# Silence noisy libraries — only show warnings/errors from them
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("pymongo.command").setLevel(logging.WARNING)
logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)
# Keep uvicorn access logs visible
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info("🚀 [Server] Starting Personalized Learning System backend...")

from database.db import db 
from auth.security import get_current_user
from bson import ObjectId

# Import Orchestrator
from Services.cartesia_orchestrator import CartesiaVideoOrchestrator

# Import Chat Router
from controller.chat_router import router as chat_router
from controller.pdf_router import router as pdf_router
from database.chat_operations import ensure_chat_indexes

load_dotenv()

app = FastAPI()

# ═════════════════════════════════════════════════════════════════════════════
# REQUEST LOGGING MIDDLEWARE — Prints every request to stdout for visibility
# ═════════════════════════════════════════════════════════════════════════════
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request and response time."""
    start = time.time()
    method = request.method
    path = request.url.path
    
    # Skip noisy static file requests
    if not path.startswith("/static"):
        print(f"\n{'─'*50}")
        print(f"📥 {method} {path}")
        print(f"{'─'*50}")
    
    response = await call_next(request)
    
    duration = time.time() - start
    if not path.startswith("/static"):
        status = response.status_code
        emoji = "✅" if status < 400 else "⚠️" if status < 500 else "❌"
        print(f"   {emoji} {method} {path} → {status} ({duration:.2f}s)")
    
    return response

# Register Chat API Router
app.include_router(chat_router)

# Register PDF RAG Router
app.include_router(pdf_router)

# Mount output directory for providing video files
# Ensure output directory exists
os.makedirs("output", exist_ok=True)
app.mount("/static", StaticFiles(directory="output"), name="static")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")

# --- Models ---
class GenerateRequest(BaseModel):
    prompt: str

class VideoProject(BaseModel):
    id: str
    prompt: str
    status: str  # pending, processing, completed, failed
    created_at: str
    video_url: Optional[str] = None
    manim_code_url: Optional[str] = None
    error: Optional[str] = None

def serialize_project(project) -> dict:
    return {
        "id": str(project["_id"]),
        "prompt": project.get("prompt"),
        "status": project.get("status"),
        "created_at": project.get("created_at").isoformat() if isinstance(project.get("created_at"), datetime.datetime) else project.get("created_at"),
        "video_url": project.get("video_url"),
        "manim_code_url": project.get("manim_code_url"),
        "error": project.get("error")
    }

# --- Background Task ---
async def generate_video_task(project_id: str, prompt: str):
    """
    Background task to run the video generation pipeline.
    Updates MongoDB with progress and results.
    """
    try:
        print("\n" + "═"*60)
        print(f"🚀 [BACKGROUND TASK] Starting generation pipeline")
        print(f"   🆔 Project ID: {project_id}")
        print(f"   📝 Prompt: {prompt}")
        print("═"*60)
        
        # 1. Update status to processing
        print(f"   🔄 [DB] Updating status to 'processing'...")
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": "processing"}}
        )

        # 2. Run Orchestrator
        print(f"   🛠️ [Orchestrator] Initializing CartesiaVideoOrchestrator...")
        print(f"   ℹ️ [Note] Currently using ONLY 'Cartesia TTS' engine for this flow.")
        
        # Initialize orchestrator (fast, lightweight)
        orchestrator = CartesiaVideoOrchestrator(output_dir="output")
        
        print(f"   ⚡ [Pipeline] Calling orchestrator.generate_video(). This may take 2-4 minutes...")
        
        # CRITICAL FIX: Run blocking synchronous code in a threadpool to prevent blocking the async event loop
        # This prevents the whole server from freezing during video generation
        result = await run_in_threadpool(orchestrator.generate_video, prompt, verbose=True)

        if result["success"]:
            print(f"\n   ✨ [Pipeline] Orchestrator completed successfully!")
            # Construct URLs
            video_path = Path(result["final_video_path"])
            manim_path = Path(result["manim_code_path"])
            
            video_filename = video_path.name
            manim_filename = manim_path.name
            
            base_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
            video_url = f"{base_url}/static/{video_filename}"
            manim_url = f"{base_url}/static/{manim_filename}"

            print(f"   🔗 [Result] Video URL: {video_url}")
            print(f"   🔗 [Result] Code URL: {manim_url}")

            print(f"   💾 [DB] Saving final URLs to project {project_id}...")
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {
                    "status": "completed",
                    "video_url": video_url,
                    "manim_code_url": manim_url
                }}
            )
            print(f"✅ [Task] Project {project_id} marked as COMPLETED.")
        else:
            error_msg = result.get('error', 'Orchestrator reported failure.')
            print(f"\n❌ [Task] Generation failed: {error_msg}")
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {
                    "status": "failed",
                    "error": f"Orchestrator error: {error_msg}"
                }}
            )

    except Exception as e:
        print(f"\n🔥 [Task] CRITICAL EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {
                "status": "failed",
                "error": f"System exception: {str(e)}"
            }}
        )

# ✅ CREATE COLLECTION ON STARTUP
@app.on_event("startup")
async def startup_event():
    """Create users collection and indexes if they don't exist"""
    print("\n" + "🏗️ "*15)
    print("🚀 BACKEND SERVER STARTING UP")
    print("🛠️  ACTIVE ORCHESTRATOR: CartesiaVideoOrchestrator")
    print("🔊 TTS ENGINE: Cartesia (WebSocket-based)")
    print("🏗️ "*15 + "\n")
    try:
        # Initialize chat indexes
        await ensure_chat_indexes()

        # Initialize PDF metadata indexes
        await db.chat_pdfs.create_index(
            [("chat_id", 1), ("user_id", 1)],
            name="idx_chat_pdfs_chat_user",
        )
        print("✅ Created chat_pdfs indexes")
        
        # Get list of existing collections
        collections = await db.list_collection_names()
        
        if "users" not in collections:
            # Create collection
            await db.create_collection("users")
            print("✅ Created 'users' collection")
            
            # Create unique index on clerk_id for faster lookups
            await db.users.create_index("clerk_id", unique=True)
            print("✅ Created unique index on clerk_id")
        else:
            print("✅ 'users' collection already exists")
    except Exception as e:
        print(f"⚠️ Startup error: {e}")

@app.get("/")
async def root():
    return {"message": "Meow! Backend is running."}

# Route 1: Protected by SDK
@app.get("/api/users/me")
async def read_users_me(user_session: dict = Depends(get_current_user)):
    return {
        "message": "Authenticated via Clerk SDK!",
        "user_data": user_session
    }

# --- Video Generation Routes ---

@app.post("/api/generate")
async def api_generate_video(
    req: GenerateRequest, 
    background_tasks: BackgroundTasks, 
    user_session: dict = Depends(get_current_user)
):
    """
    Start a video generation job.
    """
    user_id = user_session.get("sub")
    print(f"\n📥 [API] Received generation request from user: {user_id}")
    print(f"   📝 Prompt: \"{req.prompt}\"")
    
    # Create project entry
    new_project = {
        "user_id": user_id,
        "prompt": req.prompt,
        "status": "pending",
        "created_at": datetime.datetime.utcnow(),
        "video_url": None,
        "error": None
    }
    
    print(f"   📂 [DB] Creating pending project entry in MongoDB...")
    result = await db.projects.insert_one(new_project)
    project_id = str(result.inserted_id)
    print(f"   ✅ [DB] Project created with ID: {project_id}")
    
    # Trigger background task
    print(f"   ⚙️ [System] Queueing background task for execution...")
    background_tasks.add_task(generate_video_task, project_id, req.prompt)
    
    return {"status": "queued", "project_id": project_id}

@app.get("/api/projects")
async def get_user_projects(user_session: dict = Depends(get_current_user)):
    """
    Get all projects for the current user.
    """
    user_id = user_session.get("sub")
    cursor = db.projects.find({"user_id": user_id}).sort("created_at", -1)
    projects = await cursor.to_list(length=20)
    
    return [serialize_project(p) for p in projects]

@app.get("/api/projects/{project_id}")
async def get_project_status(project_id: str, user_session: dict = Depends(get_current_user)):
    """
    Get status of a specific project.
    """
    user_id = user_session.get("sub")
    
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id), "user_id": user_id})
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")
        
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return serialize_project(project)

# Route 2: Webhook
@app.post("/api/webhooks/clerk")
async def clerk_webhook(request: Request):
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Missing CLERK_WEBHOOK_SECRET")

    headers = request.headers
    payload = await request.body()
    
    try:
        wh = Webhook(WEBHOOK_SECRET)
        evt = wh.verify(payload, dict(headers))
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Webhook Signature")

    event_type = evt.get("type")
    data = evt.get("data")

    print(f"Received event: {event_type}")

    if event_type == "user.created":
        email_addr = data["email_addresses"][0]["email_address"] if data.get("email_addresses") else None
        
        new_user = {
            "clerk_id": data["id"],
            "email": email_addr,
            "first_name": data.get("first_name"),
            "role": "student"
        }
        
        # Insert into MongoDB
        result = await db.users.update_one(
            {"clerk_id": new_user["clerk_id"]},
            {"$set": new_user},
            upsert=True
        )
        
        print(f"✅ User {new_user['email']} synced to DB!")
        print(f"   Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted: {result.upserted_id}")

    return {"status": "success"}


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT — Run with: python server.py
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    print("\n" + "━" * 60)
    print("🚀 Starting server with full logging enabled")
    print("━" * 60 + "\n")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )