"""
Chat API Router — All chat-related endpoints.
Handles the complete message flow:
  User Message → Classify → Route (Video / Text) → Respond → Store in DB
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from starlette.concurrency import run_in_threadpool
import os

from auth.security import get_current_user
from Services.gemini_chat_service import GeminiChatService
from Services.cartesia_orchestrator import CartesiaVideoOrchestrator
from prompts.modes import get_all_modes_metadata, AVAILABLE_MODES, DEFAULT_MODE
from database.chat_operations import (
    create_chat,
    get_user_chats,
    get_chat_by_id,
    update_chat_title,
    archive_chat,
    save_message,
    get_chat_messages,
    get_recent_history,
    auto_title_chat,
)
from database.db import db
from bson import ObjectId

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize services
gemini_service = GeminiChatService()


# ═════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═════════════════════════════════════════════════════════════════════════════

class SendMessageRequest(BaseModel):
    chat_id: Optional[str] = None  # If None, creates a new chat
    message: str
    mode: Optional[str] = None  # Teaching mode: socratic, quiz, casual, eli5, exam_prep


class CreateChatRequest(BaseModel):
    title: Optional[str] = None


class UpdateTitleRequest(BaseModel):
    title: str


# ═════════════════════════════════════════════════════════════════════════════
# CHAT CRUD ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/modes")
async def api_get_modes():
    """Return available teaching modes for the frontend."""
    return get_all_modes_metadata()


@router.post("/create")
async def api_create_chat(
    req: CreateChatRequest,
    user_session: dict = Depends(get_current_user),
):
    """Create a new chat session."""
    user_id = user_session.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    chat = await create_chat(user_id, req.title)
    return chat


@router.get("/list")
async def api_list_chats(user_session: dict = Depends(get_current_user)):
    """Get all chats for current user."""
    user_id = user_session.get("sub")
    chats = await get_user_chats(user_id)
    return chats


@router.get("/{chat_id}")
async def api_get_chat(
    chat_id: str,
    user_session: dict = Depends(get_current_user),
):
    """Get a specific chat by ID."""
    user_id = user_session.get("sub")
    chat = await get_chat_by_id(chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.get("/{chat_id}/messages")
async def api_get_messages(
    chat_id: str,
    limit: int = 50,
    user_session: dict = Depends(get_current_user),
):
    """Get messages for a chat (paginated)."""
    user_id = user_session.get("sub")

    # Verify chat belongs to user
    chat = await get_chat_by_id(chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = await get_chat_messages(chat_id, user_id, limit=limit)
    return messages


@router.patch("/{chat_id}/title")
async def api_update_title(
    chat_id: str,
    req: UpdateTitleRequest,
    user_session: dict = Depends(get_current_user),
):
    """Update chat title."""
    user_id = user_session.get("sub")
    success = await update_chat_title(chat_id, user_id, req.title)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "updated"}


@router.delete("/{chat_id}")
async def api_archive_chat(
    chat_id: str,
    user_session: dict = Depends(get_current_user),
):
    """Soft-delete (archive) a chat."""
    user_id = user_session.get("sub")
    success = await archive_chat(chat_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "archived"}


# ═════════════════════════════════════════════════════════════════════════════
# MAIN MESSAGE ENDPOINT — THE CORE FLOW
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/send")
async def api_send_message(
    req: SendMessageRequest,
    background_tasks: BackgroundTasks,
    user_session: dict = Depends(get_current_user),
):
    """
    THE MAIN ENDPOINT. Full message flow:
    
    1. Create chat if needed
    2. Classify message (Gemini call #1)
    3. Route:
       - VIDEO → Start Cartesia orchestrator in background, return pending status
       - TEXT  → Generate response (Gemini call #2 with last 20 messages context)
    4. Save message + response to MongoDB
    5. Return complete response to frontend
    """
    user_id = user_session.get("sub")
    user_message = req.message.strip()
    active_mode = req.mode if req.mode in AVAILABLE_MODES else DEFAULT_MODE

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    print(f"\n{'═'*60}")
    print(f"📨 [Chat] New message from user {user_id}")
    print(f"   Message: '{user_message[:80]}...'")
    print(f"   Mode: {active_mode}")
    print(f"{'═'*60}")

    # ── Step 1: Ensure chat exists ──────────────────────────────────────
    chat_id = req.chat_id
    is_new_chat = False

    if not chat_id:
        chat = await create_chat(user_id)
        chat_id = chat["id"]
        is_new_chat = True
        print(f"   🆕 New chat created: {chat_id}")
    else:
        # Verify ownership
        chat = await get_chat_by_id(chat_id, user_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

    # ── Step 2: Classify message (Gemini API call #1) ───────────────────
    print(f"   🔀 [Chat] Starting message classification...")
    classification = await run_in_threadpool(
        gemini_service.classify_message, user_message
    )
    category = classification["category"]
    print(f"   🏷️ [Chat] Classification complete: {category} (reason: {classification['reason']})")

    # ── Step 3: Route based on classification ───────────────────────────
    if category == "need_video_visualisation":
        # ── VIDEO PIPELINE ──────────────────────────────────────────────
        print(f"   🎬 [Chat] Routing to VIDEO pipeline — starting generation...")

        # Save message immediately with pending video status
        saved_msg = await save_message(
            chat_id=chat_id,
            user_id=user_id,
            user_message=user_message,
            classification=classification,
            routed_to="video_generation",
            system_response="🎬 Generating your visualization... This may take 2-4 minutes.",
            video_url=None,  # Will be updated when video is ready
        )

        # Create a project entry for tracking (reuse existing project system)
        import datetime
        new_project = {
            "user_id": user_id,
            "prompt": user_message,
            "status": "pending",
            "created_at": datetime.datetime.utcnow(),
            "video_url": None,
            "error": None,
            "chat_id": chat_id,
            "message_id": saved_msg["id"],
        }
        project_result = await db.projects.insert_one(new_project)
        project_id = str(project_result.inserted_id)

        # Start video generation in background
        background_tasks.add_task(
            _generate_video_and_update_message,
            project_id=project_id,
            chat_id=chat_id,
            message_id=saved_msg["id"],
            user_id=user_id,
            prompt=user_message,
        )

        # Auto-title on first message
        if is_new_chat:
            await auto_title_chat(chat_id, user_id, user_message)

        print(f"   ✅ [Chat] Video generation started (project_id: {project_id})")
        return {
            "message": saved_msg,
            "chat_id": chat_id,
            "is_new_chat": is_new_chat,
            "status": "video_generating",
            "project_id": project_id,
        }

    elif category == "need_rag_search":
        # ── RAG/PDF SEARCH PIPELINE ─────────────────────────────────────
        print(f"   📄 [Chat] Routing to RAG SEARCH pipeline — searching uploaded PDFs...")
        
        # Check if chat has PDFs
        pdf_count = await db.chat_pdfs.count_documents({"chat_id": chat_id})
        if pdf_count == 0:
            print(f"   ⚠️ [Chat] User asked about PDFs but none are uploaded!")
            ai_response = "📚 It looks like you're asking about your notes, but I don't see any PDFs uploaded yet. Please upload your document first using the 'View PDF' button, then ask me about it!"
        else:
            print(f"   📄 [Chat] Chat has {pdf_count} PDF(s) — performing RAG search...")
            try:
                from database.qdrant import get_rag_service
                rag_service = get_rag_service()
                rag_context = await run_in_threadpool(
                    rag_service.get_rag_context,
                    query=user_message,
                    chat_id=chat_id,
                    top_k=5,
                )
                if rag_context:
                    print(f"   ✅ [Chat] RAG context retrieved ({len(rag_context)} chars)")
                    # Generate response using RAG context
                    chat_history = await get_recent_history(chat_id, user_id, limit=20)
                    ai_response = await run_in_threadpool(
                        gemini_service.generate_text_response,
                        user_message,
                        chat_history,
                        active_mode,
                        rag_context,
                    )
                else:
                    print(f"   ℹ️ [Chat] RAG search returned no relevant results")
                    ai_response = "📚 I searched through your uploaded documents but didn't find information directly related to your question. Could you rephrase it or upload more relevant material?"
            except Exception as e:
                print(f"   ❌ [Chat] RAG search failed: {e}")
                ai_response = f"⚠️ I had trouble searching your documents. Please try again: {str(e)[:100]}"

        # Save complete message to DB
        saved_msg = await save_message(
            chat_id=chat_id,
            user_id=user_id,
            user_message=user_message,
            classification=classification,
            routed_to="rag_search",
            system_response=ai_response,
        )
        print(f"   💾 [Chat] RAG message saved to database (id: {saved_msg['id']})")

        # Auto-title on first message
        if is_new_chat:
            await auto_title_chat(chat_id, user_id, user_message)

        print(f"   🎉 [Chat] RAG search completed successfully")

        return {
            "message": saved_msg,
            "chat_id": chat_id,
            "is_new_chat": is_new_chat,
            "status": "completed",
        }

    else:
        # ── TEXT PIPELINE (DEFAULT) ─────────────────────────────────────
        print(f"   💬 [Chat] Routing to TEXT pipeline — generating response...")

        # Fetch last 20 messages for context
        chat_history = await get_recent_history(chat_id, user_id, limit=20)
        print(f"   📚 [Chat] Retrieved {len(chat_history)} messages for context")

        # ── RAG: Optionally check if this chat has uploaded PDFs ────────
        rag_context = None
        try:
            pdf_count = await db.chat_pdfs.count_documents({"chat_id": chat_id})
            if pdf_count > 0:
                print(f"   📄 [Chat] Chat has {pdf_count} PDF(s) — performing optional RAG search...")
                from database.qdrant import get_rag_service
                rag_service = get_rag_service()
                rag_context = await run_in_threadpool(
                    rag_service.get_rag_context,
                    query=user_message,
                    chat_id=chat_id,
                    top_k=5,
                )
                if rag_context:
                    print(f"   ✅ [Chat] RAG context retrieved ({len(rag_context)} chars)")
                else:
                    print(f"   ℹ️ [Chat] RAG search returned no relevant results")
            else:
                print(f"   ℹ️ [Chat] No PDFs in this chat — skipping RAG")
        except Exception as e:
            print(f"   ⚠️ [Chat] RAG search failed (non-fatal): {e}")
            rag_context = None

        # Generate text response (Gemini API call #2 with context + mode + optional RAG)
        print(f"   🤖 [Chat] Calling Gemini for text response (mode: {active_mode}, RAG: {'YES' if rag_context else 'NO'})...")
        ai_response = await run_in_threadpool(
            gemini_service.generate_text_response,
            user_message,
            chat_history,
            active_mode,
            rag_context,
        )
        print(f"   ✅ [Chat] Text response generated ({len(ai_response)} chars)")

        # Save complete message to DB
        saved_msg = await save_message(
            chat_id=chat_id,
            user_id=user_id,
            user_message=user_message,
            classification=classification,
            routed_to="text_response",
            system_response=ai_response,
        )
        print(f"   💾 [Chat] Message saved to database (id: {saved_msg['id']})")

        # Auto-title on first message
        if is_new_chat:
            await auto_title_chat(chat_id, user_id, user_message)

        print(f"   🎉 [Chat] Text response sent successfully")

        return {
            "message": saved_msg,
            "chat_id": chat_id,
            "is_new_chat": is_new_chat,
            "status": "completed",
        }


# ═════════════════════════════════════════════════════════════════════════════
# BACKGROUND VIDEO GENERATION TASK
# ═════════════════════════════════════════════════════════════════════════════

async def _generate_video_and_update_message(
    project_id: str,
    chat_id: str,
    message_id: str,
    user_id: str,
    prompt: str,
):
    """
    Background task: Generate video via Cartesia orchestrator,
    then update the chat message with the video URL.
    Uses intelligent filename generation based on prompt content.
    """
    from pathlib import Path
    from database.chat_operations import messages_collection

    try:
        print(f"\n🎬 [VideoTask] Starting video generation for message {message_id}")
        print(f"   📝 Prompt: {prompt}")

        # Update project status
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": "processing"}},
        )

        # Run orchestrator with chat/message context for filename generation
        orchestrator = CartesiaVideoOrchestrator(
            output_dir="output",
            chat_id=chat_id,
            message_id=message_id
        )
        result = await run_in_threadpool(orchestrator.generate_video, prompt, verbose=True)

        if result["success"]:
            # Get the intelligently generated filename
            video_filename = result.get("video_filename") or Path(result["final_video_path"]).name
            base_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
            video_url = f"{base_url}/static/{video_filename}"

            print(f"   📝 [VideoTask] Intelligent filename: {video_filename}")

            # Update the chat message with video URL
            await messages_collection.update_one(
                {"_id": ObjectId(message_id)},
                {
                    "$set": {
                        "video_url": video_url,
                        "system_response": "Here's your visualization!",
                        "updated_at": __import__("datetime").datetime.utcnow(),
                    }
                },
            )

            # Update project
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {
                    "$set": {
                        "status": "completed",
                        "video_url": video_url,
                    }
                },
            )

            print(f"   ✅ [VideoTask] Video ready: {video_url}")

        else:
            error_msg = result.get("error", "Video generation failed")
            await messages_collection.update_one(
                {"_id": ObjectId(message_id)},
                {
                    "$set": {
                        "system_response": f"Sorry, video generation failed: {error_msg}",
                        "updated_at": __import__("datetime").datetime.utcnow(),
                    }
                },
            )
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"status": "failed", "error": error_msg}},
            )
            print(f"   ❌ [VideoTask] Failed: {error_msg}")

    except Exception as e:
        print(f"   🔥 [VideoTask] Exception: {e}")
        import traceback
        traceback.print_exc()

        await messages_collection.update_one(
            {"_id": ObjectId(message_id)},
            {
                "$set": {
                    "system_response": f"Video generation encountered an error: {str(e)}",
                    "updated_at": __import__("datetime").datetime.utcnow(),
                }
            },
        )
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": "failed", "error": str(e)}},
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIDEO STATUS POLLING ENDPOINT
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/video-status/{project_id}")
async def api_video_status(
    project_id: str,
    user_session: dict = Depends(get_current_user),
):
    """Poll for video generation status. Frontend calls this while video is generating."""
    user_id = user_session.get("sub")

    try:
        project = await db.projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": user_id,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "status": project.get("status"),
        "video_url": project.get("video_url"),
        "error": project.get("error"),
    }


@router.get("/message/{message_id}")
async def api_get_message(
    message_id: str,
    user_session: dict = Depends(get_current_user),
):
    """Get a single message by ID (used to poll for video URL updates)."""
    user_id = user_session.get("sub")
    from database.chat_operations import messages_collection, serialize_message

    try:
        msg = await messages_collection.find_one({
            "_id": ObjectId(message_id),
            "user_id": user_id,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    return serialize_message(msg)
