from beanie import Document
from pydantic import Field
from uuid import UUID, uuid4
from datetime import datetime

class User(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Settings:
        name = "users"
        indexes = [
            "email",
        ]
