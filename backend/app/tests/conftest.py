import pytest
import pytest_asyncio
import os
import io
import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient
import fakeredis.aioredis

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.document import Document, FileType, DocumentStatus
from app.models.transcript import TranscriptSegment

# Ensure uploads go to a temp directory
settings.UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "_test_uploads")
settings.MAX_FILE_SIZE_MB = 500
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


# ─── Event loop fixture ──────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─── Initialize Beanie with mongomock ─────────────────
@pytest_asyncio.fixture(autouse=True)
async def init_db():
    client = AsyncMongoMockClient()
    db = client["test_db"]

    # Monkey-patch: mongomock doesn't accept the authorizedCollections kwarg
    # that newer Beanie/Motor versions pass to list_collection_names().
    _original = db.list_collection_names.__wrapped__ if hasattr(db.list_collection_names, '__wrapped__') else None

    import mongomock_motor
    _orig_method = db.delegate.list_collection_names

    def _patched_list_collection_names(*args, **kwargs):
        kwargs.pop("authorizedCollections", None)
        kwargs.pop("nameOnly", None)
        return _orig_method(*args, **kwargs)

    db.delegate.list_collection_names = _patched_list_collection_names

    await init_beanie(
        database=db,
        document_models=[User, Document, TranscriptSegment],
    )
    yield
    # Clean all collections after each test
    await User.delete_all()
    await Document.delete_all()
    await TranscriptSegment.delete_all()


# ─── Patch database init so the app lifespan doesn't touch real DB ──
@pytest_asyncio.fixture(autouse=True)
async def patch_db_init():
    with patch("app.core.database.init_db", new_callable=AsyncMock):
        with patch("app.core.database.close_db", new_callable=AsyncMock):
            yield


# ─── Async test client ────────────────────────────────
@pytest_asyncio.fixture
async def async_client(patch_db_init):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ─── Pre-created test user + auth header ──────────────
@pytest_asyncio.fixture
async def test_user():
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
    )
    await user.insert()
    token = create_access_token(user.id)
    return {"user": user, "token": token}


@pytest.fixture
def auth_headers(test_user):
    return {"Authorization": f"Bearer {test_user['token']}"}


# ─── Sample files ─────────────────────────────────────
@pytest.fixture
def sample_pdf_file():
    """Minimal valid PDF file bytes."""
    content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Hello World) Tj ET
endstream
endobj
xref
0 5
trailer
<< /Size 5 /Root 1 0 R >>
startxref
0
%%EOF"""
    return ("test.pdf", io.BytesIO(content), "application/pdf")


@pytest.fixture
def sample_audio_file():
    """Tiny WAV file header (44-byte minimal header + 100 bytes of silence)."""
    import struct

    sample_rate = 8000
    num_samples = 100
    data_size = num_samples * 2  # 16-bit mono
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,      # PCM
        1,      # channels
        sample_rate,
        sample_rate * 2,
        2,      # block align
        16,     # bits per sample
        b"data",
        data_size,
    )
    audio_data = b"\x00" * data_size
    return ("test.wav", io.BytesIO(header + audio_data), "audio/wav")


@pytest.fixture
def sample_video_file():
    """Fake video file (just enough bytes for magic to read)."""
    # ftyp box header for a fake MP4
    content = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 2048
    return ("test.mp4", io.BytesIO(content), "video/mp4")


@pytest.fixture
def oversized_file():
    """A file that exceeds MAX_FILE_SIZE_MB — headers claim 600MB."""
    content = b"\x00" * (1024 * 10)  # 10KB actual, but we'll patch the size check
    return ("big.pdf", io.BytesIO(content), "application/pdf")


# ─── Mock Gemini Chat ─────────────────────────────────
@pytest.fixture
def mock_openai():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mock AI answer."

    with patch("app.services.ai_service.ChatGoogleGenerativeAI") as mock_cls:
        instance = MagicMock()
        instance.acall = AsyncMock(return_value={"result": "Mock answer", "source_documents": []})
        instance.arun = AsyncMock(return_value="Mock summary of the document.")
        instance.astream = MagicMock(return_value=_async_token_gen())
        mock_cls.return_value = instance
        yield instance


async def _async_token_gen():
    tokens = ["This ", "is ", "a ", "mock ", "streamed ", "answer."]
    for t in tokens:
        chunk = MagicMock()
        chunk.content = t
        yield chunk


# ─── Mock Whisper ─────────────────────────────────────
@pytest.fixture
def mock_whisper():
    mock_result = {
        "text": "Hello, this is a test transcription.",
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "Hello, this is"},
            {"start": 2.5, "end": 5.0, "text": "a test transcription."},
        ],
    }
    mock_response = MagicMock()
    mock_response.model_dump.return_value = mock_result

    with patch("app.services.transcription_service.client") as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
        yield mock_client


# ─── Mock Redis ───────────────────────────────────────
@pytest.fixture
def mock_redis():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch("app.services.ai_service.ChatService.__init__", lambda self: None):
        yield fake


# ─── Mock python-magic ────────────────────────────────
@pytest.fixture
def mock_magic_pdf():
    with patch("app.services.file_service.magic.from_buffer", return_value="application/pdf"):
        yield


@pytest.fixture
def mock_magic_audio():
    with patch("app.services.file_service.magic.from_buffer", return_value="audio/mpeg"):
        yield


@pytest.fixture
def mock_magic_video():
    with patch("app.services.file_service.magic.from_buffer", return_value="video/mp4"):
        yield


@pytest.fixture
def mock_magic_unsupported():
    with patch("app.services.file_service.magic.from_buffer", return_value="application/x-executable"):
        yield
