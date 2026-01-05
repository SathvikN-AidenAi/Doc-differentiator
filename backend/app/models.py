from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    comparisons = relationship("Comparison", back_populates="session", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    text_cache = relationship("ExtractedTextCache", back_populates="session", cascade="all, delete-orphan", uselist=False)

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(10), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="documents")

    __table_args__ = (
        CheckConstraint("document_type IN ('before', 'after')", name="check_document_type"),
        UniqueConstraint("session_id", "document_type", name="uq_session_document_type"),
    )

class Comparison(Base):
    __tablename__ = "comparisons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    before_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    after_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    result_json = Column(JSONB, nullable=False)
    pages_before = Column(Integer)
    pages_after = Column(Integer)
    diff_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="comparisons")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    message_order = Column(Integer, nullable=False)

    session = relationship("Session", back_populates="chat_messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="check_role"),
    )

class ExtractedTextCache(Base):
    __tablename__ = "extracted_text_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    before_text = Column(Text)
    after_text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="text_cache")
