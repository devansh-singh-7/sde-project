from beanie import Document, Link
from pydantic import Field
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional
from app.models.user import User

class FileType(str, Enum):
    PDF = "PDF"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"

class DocumentStatus(str, Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"

class Document(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Link[User]  # Reference to the User Document
    filename: str
    file_type: FileType
    file_path: str
    transcript_text: Optional[str] = None
    summary: Optional[str] = None
    vector_store_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: DocumentStatus = DocumentStatus.PROCESSING

    class Settings:
        name = "documents"
