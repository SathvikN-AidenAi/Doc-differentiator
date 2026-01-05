from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, UUID4
from uuid import UUID

class SessionCreate(BaseModel):
    pass

class SessionResponse(BaseModel):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime

    class Config:
        from_attributes = True

class DocumentUpload(BaseModel):
    original_filename: str
    document_type: str

class DocumentResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    document_type: str
    original_filename: str
    file_size_bytes: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ComparisonResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    result_json: Dict[str, Any]
    pages_before: Optional[int]
    pages_after: Optional[int]
    diff_count: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    role: str
    content: str

class ChatMessageResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    role: str
    content: str
    created_at: datetime
    message_order: int

    class Config:
        from_attributes = True

class SessionDataResponse(BaseModel):
    session: SessionResponse
    documents: List[DocumentResponse]
    comparison: Optional[ComparisonResponse]
    chat_messages: List[ChatMessageResponse]
