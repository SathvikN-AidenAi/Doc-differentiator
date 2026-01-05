from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.models import Session, Document, Comparison, ChatMessage, ExtractedTextCache
from app.config import settings

# Session operations
async def create_session(db: AsyncSession) -> Session:
    session = Session()
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def get_session(db: AsyncSession, session_id: UUID) -> Optional[Session]:
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    return result.scalar_one_or_none()

async def update_session_access(db: AsyncSession, session_id: UUID):
    session = await get_session(db, session_id)
    if session:
        session.last_accessed = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        await db.commit()

async def get_session_with_data(db: AsyncSession, session_id: UUID) -> Optional[Session]:
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.documents),
            selectinload(Session.comparisons),
            selectinload(Session.chat_messages),
            selectinload(Session.text_cache)
        )
        .where(Session.id == session_id)
    )
    return result.scalar_one_or_none()

# Document operations
async def create_document(
    db: AsyncSession,
    session_id: UUID,
    document_type: str,
    original_filename: str,
    stored_filename: str,
    file_path: str,
    file_size_bytes: int
) -> Document:
    # Delete existing document of same type for this session
    await db.execute(
        delete(Document).where(
            Document.session_id == session_id,
            Document.document_type == document_type
        )
    )

    document = Document(
        session_id=session_id,
        document_type=document_type,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size_bytes=file_size_bytes
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document

async def get_documents_by_session(db: AsyncSession, session_id: UUID) -> List[Document]:
    result = await db.execute(
        select(Document).where(Document.session_id == session_id)
    )
    return list(result.scalars().all())

# Comparison operations
async def create_or_update_comparison(
    db: AsyncSession,
    session_id: UUID,
    before_document_id: UUID,
    after_document_id: UUID,
    result_json: dict
) -> Comparison:
    # Check if comparison exists
    result = await db.execute(
        select(Comparison).where(Comparison.session_id == session_id)
    )
    comparison = result.scalar_one_or_none()

    if comparison:
        comparison.before_document_id = before_document_id
        comparison.after_document_id = after_document_id
        comparison.result_json = result_json
        comparison.pages_before = result_json.get("pages_before")
        comparison.pages_after = result_json.get("pages_after")
        comparison.diff_count = len(result_json.get("diffs", []))
    else:
        comparison = Comparison(
            session_id=session_id,
            before_document_id=before_document_id,
            after_document_id=after_document_id,
            result_json=result_json,
            pages_before=result_json.get("pages_before"),
            pages_after=result_json.get("pages_after"),
            diff_count=len(result_json.get("diffs", []))
        )
        db.add(comparison)

    await db.commit()
    await db.refresh(comparison)
    return comparison

async def get_comparison_by_session(db: AsyncSession, session_id: UUID) -> Optional[Comparison]:
    result = await db.execute(
        select(Comparison).where(Comparison.session_id == session_id)
    )
    return result.scalar_one_or_none()

# Chat message operations
async def create_chat_message(
    db: AsyncSession,
    session_id: UUID,
    role: str,
    content: str
) -> ChatMessage:
    # Get current message count for ordering
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    message_count = len(list(result.scalars().all()))

    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        message_order=message_count
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

async def get_chat_messages(db: AsyncSession, session_id: UUID) -> List[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.message_order)
    )
    return list(result.scalars().all())

# Text cache operations
async def create_or_update_text_cache(
    db: AsyncSession,
    session_id: UUID,
    before_text: str,
    after_text: str
) -> ExtractedTextCache:
    result = await db.execute(
        select(ExtractedTextCache).where(ExtractedTextCache.session_id == session_id)
    )
    cache = result.scalar_one_or_none()

    if cache:
        cache.before_text = before_text
        cache.after_text = after_text
    else:
        cache = ExtractedTextCache(
            session_id=session_id,
            before_text=before_text,
            after_text=after_text
        )
        db.add(cache)

    await db.commit()
    await db.refresh(cache)
    return cache

async def get_text_cache(db: AsyncSession, session_id: UUID) -> Optional[ExtractedTextCache]:
    result = await db.execute(
        select(ExtractedTextCache).where(ExtractedTextCache.session_id == session_id)
    )
    return result.scalar_one_or_none()

# Cleanup operations
async def cleanup_old_sessions(db: AsyncSession):
    """Delete sessions older than SESSION_TIMEOUT_HOURS"""
    cutoff = datetime.utcnow() - timedelta(hours=settings.SESSION_TIMEOUT_HOURS)
    await db.execute(
        delete(Session).where(Session.last_accessed < cutoff)
    )
    await db.commit()
