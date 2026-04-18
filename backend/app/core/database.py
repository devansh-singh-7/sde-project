from typing import Any
from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import AsyncMongoClient
from beanie import init_beanie
from app.core.config import settings

# Import all Beanie documents models here so init_beanie can use them
from app.models.user import User
from app.models.document import Document
from app.models.transcript import TranscriptSegment

class Database:
    client: Any = None

db = Database()


def _resolve_database_name() -> str:
    parsed = urlparse(settings.DATABASE_URL)
    db_name = parsed.path.lstrip("/")
    return db_name or "ai_qa_db"


def _get_database(client: Any):
    database_name = _resolve_database_name()
    # Works for both Motor and PyMongo Async clients.
    return client.get_database(database_name)

async def init_db():
    db.client = AsyncIOMotorClient(settings.DATABASE_URL, uuidRepresentation="standard")
    database = _get_database(db.client)

    try:
        await init_beanie(
            database=database,
            document_models=[
                User,
                Document,
                TranscriptSegment
            ]
        )
    except TypeError as exc:
        # Beanie + Motor can break on newer PyMongo internals; retry with PyMongo async client.
        if "append_metadata" not in str(exc):
            raise

        db.client.close()
        db.client = AsyncMongoClient(settings.DATABASE_URL, uuidRepresentation="standard")
        database = _get_database(db.client)
        await init_beanie(
            database=database,
            document_models=[
                User,
                Document,
                TranscriptSegment
            ]
        )
        database = _get_database(db.client)
        await init_beanie(
            database=database,
            document_models=[
                User,
                Document,
                TranscriptSegment
            ]
        )

async def close_db():
    if db.client:
        db.client.close()

# get_db dependency stub for FastAPI routers if needed
async def get_db():
    return db.client
