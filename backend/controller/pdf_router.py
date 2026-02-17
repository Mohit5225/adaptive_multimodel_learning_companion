"""
PDF RAG API Router — Upload, search, and manage PDF documents for RAG.
Endpoints:
  POST   /api/pdf/upload       — Upload a PDF → extract text → ingest into Qdrant
  GET    /api/pdf/list/{chat_id} — List PDFs uploaded for a chat
  DELETE /api/pdf/{pdf_id}     — Delete a PDF's vectors from Qdrant
  POST   /api/pdf/search       — Manual RAG search (for testing)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from starlette.concurrency import run_in_threadpool
from datetime import datetime, timezone

from auth.security import get_current_user
from Services.pdf_service import extract_text_from_pdf
from database.qdrant import get_rag_service
from database.db import db

router = APIRouter(prefix="/api/pdf", tags=["pdf"])

# MongoDB collection for PDF metadata (tracks which chats have PDFs)
pdf_collection = db.chat_pdfs


# ═════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═════════════════════════════════════════════════════════════════════════════

class SearchRequest(BaseModel):
    chat_id: str
    query: str
    top_k: int = 5


# ═════════════════════════════════════════════════════════════════════════════
# PDF UPLOAD — Extract text + Ingest into Qdrant
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/upload")
async def api_upload_pdf(
    file: UploadFile = File(...),
    chat_id: str = Form(...),
    user_session: dict = Depends(get_current_user),
):
    """
    Upload a PDF file for RAG context in a specific chat.
    1. Validates the file is a PDF
    2. Extracts text using PyMuPDF
    3. Chunks and ingests into Qdrant with Jina embeddings
    """
    user_id = user_session.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid content type — expected application/pdf")

    print(f"\n📄 [PDF Upload] File: {file.filename}")
    print(f"   👤 User: {user_id}")
    print(f"   💬 Chat: {chat_id}")

    # Read file bytes
    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(pdf_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="PDF file too large (max 20MB)")

    print(f"   📦 Size: {len(pdf_bytes) / 1024:.1f} KB")

    # Extract text
    try:
        text = await run_in_threadpool(extract_text_from_pdf, pdf_bytes)
    except Exception as e:
        print(f"   ❌ [PDF] Text extraction failed: {e}")
        raise HTTPException(status_code=422, detail=f"Could not extract text from PDF: {str(e)}")

    if not text or len(text.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="PDF appears to be empty or contains too little extractable text (scanned images are not supported yet)",
        )

    print(f"   📝 Extracted text: {len(text)} chars")

    # Ingest into Qdrant
    try:
        rag_service = get_rag_service()
        result = await run_in_threadpool(
            rag_service.ingest_document,
            text=text,
            chat_id=chat_id,
            user_id=user_id,
            filename=file.filename,
        )
    except Exception as e:
        print(f"   ❌ [Qdrant] Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF: {str(e)}")

    print(f"   ✅ [PDF Upload] Complete — {result['chunks']} chunks stored")

    # Store PDF metadata in MongoDB so we know this chat has PDFs
    pdf_doc = {
        "pdf_id": result["pdf_id"],
        "chat_id": chat_id,
        "user_id": user_id,
        "filename": file.filename,
        "chunks": result["chunks"],
        "text_length": len(text),
        "created_at": datetime.now(timezone.utc),
    }
    await pdf_collection.insert_one(pdf_doc)
    print(f"   💾 [MongoDB] PDF metadata saved for chat {chat_id}")

    return {
        "status": "success",
        "pdf_id": result["pdf_id"],
        "filename": file.filename,
        "chunks": result["chunks"],
        "text_length": len(text),
        "message": f"PDF '{file.filename}' uploaded and indexed successfully ({result['chunks']} chunks)",
    }


# ═════════════════════════════════════════════════════════════════════════════
# LIST PDFs FOR A CHAT
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/list/{chat_id}")
async def api_list_pdfs(
    chat_id: str,
    user_session: dict = Depends(get_current_user),
):
    """List all PDFs uploaded to a specific chat (from MongoDB — fast)."""
    user_id = user_session.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        cursor = pdf_collection.find(
            {"chat_id": chat_id, "user_id": user_id},
            {"_id": 0, "pdf_id": 1, "filename": 1, "chunks": 1, "text_length": 1, "created_at": 1},
        ).sort("created_at", -1)
        pdfs = await cursor.to_list(length=50)
        # Serialize datetime
        for p in pdfs:
            if "created_at" in p:
                p["created_at"] = p["created_at"].isoformat()
        return {"chat_id": chat_id, "pdfs": pdfs, "has_pdfs": len(pdfs) > 0}
    except Exception as e:
        print(f"   ❌ [MongoDB] Failed to list PDFs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list PDFs: {str(e)}")


# ═════════════════════════════════════════════════════════════════════════════
# DELETE PDF
# ═════════════════════════════════════════════════════════════════════════════

@router.delete("/{pdf_id}")
async def api_delete_pdf(
    pdf_id: str,
    user_session: dict = Depends(get_current_user),
):
    """Delete all vectors for a specific PDF from Qdrant + MongoDB metadata."""
    user_id = user_session.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        # Delete from Qdrant
        rag_service = get_rag_service()
        await run_in_threadpool(rag_service.delete_pdf_vectors, pdf_id)
        # Delete from MongoDB
        await pdf_collection.delete_one({"pdf_id": pdf_id, "user_id": user_id})
        return {"status": "deleted", "pdf_id": pdf_id}
    except Exception as e:
        print(f"   ❌ [Qdrant] Failed to delete PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete PDF: {str(e)}")


# ═════════════════════════════════════════════════════════════════════════════
# SEARCH (TEST ENDPOINT)
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/search")
async def api_search_pdf(
    req: SearchRequest,
    user_session: dict = Depends(get_current_user),
):
    """
    Search PDFs in a chat for relevant context.
    Useful for testing the RAG pipeline manually.
    """
    user_id = user_session.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        rag_service = get_rag_service()
        results = await run_in_threadpool(
            rag_service.hybrid_search,
            query=req.query,
            chat_id=req.chat_id,
            top_k=req.top_k,
        )
        return {"query": req.query, "results": results}
    except Exception as e:
        print(f"   ❌ [Qdrant] Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
