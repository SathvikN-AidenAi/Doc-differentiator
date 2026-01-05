import io
import json
from uuid import UUID
from pypdf import PdfReader
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.diff import compare_documents
from app.database import get_db, init_db
from app.config import settings
from app import crud, schemas, storage
from app.llm_utils import stream_chat_response

app = FastAPI(title="DocDiff Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    print(f"✅ Database initialized")
    print(f"✅ Upload directory: {settings.UPLOAD_DIR}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ==================== Session Management ====================

@app.post("/sessions", response_model=schemas.SessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    """Create a new session"""
    session = await crud.create_session(db)
    return session

@app.get("/sessions/{session_id}", response_model=schemas.SessionDataResponse)
async def get_session_data(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all data for a session (documents, comparison, chat history)"""
    session = await crud.get_session_with_data(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update last accessed time
    await crud.update_session_access(db, session_id)

    # Get comparison
    comparison = await crud.get_comparison_by_session(db, session_id)

    # Get chat messages
    chat_messages = await crud.get_chat_messages(db, session_id)

    return {
        "session": session,
        "documents": session.documents,
        "comparison": comparison,
        "chat_messages": chat_messages
    }

# ==================== Document Upload & Comparison ====================

@app.post("/compare")
async def compare_docs(
    before_file: UploadFile = File(...),
    after_file: UploadFile = File(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare two uploaded PDFs and save everything to database
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    # Verify session exists
    session = await crud.get_session(db, session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Read file contents
    before_bytes = await before_file.read()
    after_bytes = await after_file.read()

    # Validate file sizes
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(before_bytes) > max_size or len(after_bytes) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Save files to disk
    before_stored, before_path, before_size = await storage.save_uploaded_file(
        before_bytes, before_file.filename, str(session_uuid), "before"
    )
    after_stored, after_path, after_size = await storage.save_uploaded_file(
        after_bytes, after_file.filename, str(session_uuid), "after"
    )

    # Save document records
    before_doc = await crud.create_document(
        db, session_uuid, "before", before_file.filename,
        before_stored, before_path, before_size
    )
    after_doc = await crud.create_document(
        db, session_uuid, "after", after_file.filename,
        after_stored, after_path, after_size
    )

    # Extract text for LLM
    before_reader = PdfReader(io.BytesIO(before_bytes))
    after_reader = PdfReader(io.BytesIO(after_bytes))
    before_text = "\n".join([p.extract_text() or "" for p in before_reader.pages])
    after_text = "\n".join([p.extract_text() or "" for p in after_reader.pages])

    # Cache extracted text
    await crud.create_or_update_text_cache(db, session_uuid, before_text, after_text)

    # Run comparison
    result = await compare_documents(
        before_bytes, after_bytes,
        before_file.filename, after_file.filename
    )

    # Save comparison results
    comparison = await crud.create_or_update_comparison(
        db, session_uuid, before_doc.id, after_doc.id, result
    )

    # Update session access time
    await crud.update_session_access(db, session_uuid)

    return result

# ==================== Chat / LLM Integration ====================

@app.post("/ask")
async def ask_llm(
    question: str = Form(...),
    diffs: str = Form(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream conversational responses from Azure OpenAI and save to database
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    # Verify session exists
    session = await crud.get_session(db, session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get chat history
    chat_messages = await crud.get_chat_messages(db, session_uuid)
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_messages
    ]

    # Save user message
    await crud.create_chat_message(db, session_uuid, "user", question)

    # Stream response
    accumulated_response = ""

    async def stream_and_save():
        nonlocal accumulated_response
        try:
            async for chunk in stream_chat_response(question, diffs, chat_history):
                accumulated_response += chunk
                yield chunk
        finally:
            # Save assistant message after streaming completes
            if accumulated_response:
                await crud.create_chat_message(db, session_uuid, "assistant", accumulated_response)
                await crud.update_session_access(db, session_uuid)

    return StreamingResponse(stream_and_save(), media_type="text/plain")

# ==================== Cleanup ====================

@app.post("/cleanup")
async def cleanup_old_sessions(db: AsyncSession = Depends(get_db)):
    """Clean up old sessions (can be called via cron)"""
    await crud.cleanup_old_sessions(db)
    return {"status": "cleanup completed"}
