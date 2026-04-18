from beanie import Document, Link
from pydantic import Field
from uuid import UUID, uuid4
from typing import List
from app.models.document import Document as DocModel

class TranscriptSegment(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: Link[DocModel]
    start_time: float
    end_time: float
    text: str
    topics: List[str] = Field(default_factory=list)

    class Settings:
        name = "transcript_segments"
