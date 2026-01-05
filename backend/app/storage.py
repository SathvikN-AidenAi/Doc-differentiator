import os
import uuid
from pathlib import Path
from typing import Tuple
from app.config import settings

def generate_stored_filename(original_filename: str, session_id: str, document_type: str) -> str:
    """
    Generate unique filename for storage
    Format: {session_id}_{document_type}_{uuid}_{original_name}
    """
    file_uuid = uuid.uuid4().hex[:8]
    safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._- ")
    return f"{session_id}_{document_type}_{file_uuid}_{safe_filename}"

def get_file_path(stored_filename: str) -> Path:
    """Get full path for stored file"""
    return settings.UPLOAD_DIR / stored_filename

async def save_uploaded_file(
    file_content: bytes,
    original_filename: str,
    session_id: str,
    document_type: str
) -> Tuple[str, str, int]:
    """
    Save uploaded file to disk
    Returns: (stored_filename, file_path, file_size_bytes)
    """
    stored_filename = generate_stored_filename(original_filename, session_id, document_type)
    file_path = get_file_path(stored_filename)

    # Write file
    with open(file_path, "wb") as f:
        f.write(file_content)

    file_size = len(file_content)
    return stored_filename, str(file_path), file_size

async def load_file(stored_filename: str) -> bytes:
    """Load file from disk"""
    file_path = get_file_path(stored_filename)
    with open(file_path, "rb") as f:
        return f.read()

def delete_file(stored_filename: str):
    """Delete file from disk"""
    file_path = get_file_path(stored_filename)
    if file_path.exists():
        file_path.unlink()
