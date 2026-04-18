import pytest
import io
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient

from app.models.document import Document, FileType, DocumentStatus
from app.models.transcript import TranscriptSegment


@pytest.mark.asyncio
class TestEndToEndFlow:
    """Full integration: register → upload → process → chat → get timestamp."""

    async def test_full_pdf_flow(self, async_client: AsyncClient):
        # ── 1. Register ──
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "e2e@example.com",
            "password": "e2e_password_123",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ── 2. Verify /me ──
        resp = await async_client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "e2e@example.com"
        user_id = resp.json()["id"]

        # ── 3. Upload PDF ──
        pdf_bytes = b"%PDF-1.4 fake content"
        with patch("app.services.file_service.magic.from_buffer", return_value="application/pdf"):
            with patch("app.api.routes.upload.process_document"):
                resp = await async_client.post(
                    "/api/v1/upload/",
                    files={"file": ("integration.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                    headers=headers,
                )
        assert resp.status_code == 200
        doc_id = resp.json()["document_id"]

        # ── 4. List documents — should have 1 ──
        resp = await async_client.get("/api/v1/upload/documents", headers=headers)
        assert resp.status_code == 200
        docs = resp.json()
        assert len(docs) == 1
        assert docs[0]["filename"] == "integration.pdf"

        # ── 5. Simulate processing completion ──
        doc = await Document.find_one(Document.id == doc_id)
        doc.status = DocumentStatus.READY
        doc.transcript_text = "This is the extracted PDF text for integration testing."
        await doc.save()

        # Add transcript segments
        seg = TranscriptSegment(
            document_id=doc.to_ref(),
            start_time=1.0,
            end_time=1.0,
            text="This is the extracted PDF text for integration testing.",
        )
        await seg.insert()

        # ── 6. Get document detail ──
        resp = await async_client.get(f"/api/v1/upload/documents/{doc_id}", headers=headers)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["document"]["status"] == "READY"
        assert len(detail["transcript_segments"]) == 1

        # ── 7. Chat with the document ──
        mock_answer = {
            "answer": "The PDF discusses integration testing.",
            "sources": [{"text": "extracted PDF text", "start_time": None, "end_time": None}],
            "relevant_timestamp": None,
        }
        with patch("app.api.routes.chat.chat_service") as mock_cs:
            mock_cs.answer_question = AsyncMock(return_value=mock_answer)
            resp = await async_client.post(
                "/api/v1/chat/",
                json={
                    "document_id": doc_id,
                    "question": "What does this PDF discuss?",
                    "chat_history": [],
                },
                headers=headers,
            )
        assert resp.status_code == 200
        assert "integration testing" in resp.json()["answer"]

        # ── 8. Summarize ──
        with patch("app.api.routes.chat.chat_service") as mock_cs:
            mock_cs.summarize_document = AsyncMock(return_value="A summary of the PDF.")
            resp = await async_client.post(
                f"/api/v1/chat/summarize/{doc_id}",
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["summary"] == "A summary of the PDF."

        # ── 9. Delete document ──
        resp = await async_client.delete(f"/api/v1/upload/documents/{doc_id}", headers=headers)
        assert resp.status_code == 204

        # ── 10. Verify gone ──
        resp = await async_client.get(f"/api/v1/upload/documents/{doc_id}", headers=headers)
        assert resp.status_code == 404

    async def test_full_audio_flow_with_timestamps(self, async_client: AsyncClient):
        # ── 1. Register ──
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "audio_e2e@example.com",
            "password": "audio_password_123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ── 2. Upload Audio ──
        audio_bytes = b"\x00" * 500  # fake
        with patch("app.services.file_service.magic.from_buffer", return_value="audio/mpeg"):
            with patch("app.api.routes.upload.process_document"):
                resp = await async_client.post(
                    "/api/v1/upload/",
                    files={"file": ("interview.mp3", io.BytesIO(audio_bytes), "audio/mpeg")},
                    headers=headers,
                )
        assert resp.status_code == 200
        doc_id = resp.json()["document_id"]

        # ── 3. Simulate processing with timestamps ──
        doc = await Document.find_one(Document.id == doc_id)
        doc.status = DocumentStatus.READY
        doc.transcript_text = "Hello welcome to the interview. Tell me about yourself."
        await doc.save()

        for start, end, text in [
            (0.0, 3.0, "Hello welcome to the interview."),
            (3.0, 8.0, "Tell me about yourself."),
        ]:
            seg = TranscriptSegment(
                document_id=doc.to_ref(),
                start_time=start,
                end_time=end,
                text=text,
            )
            await seg.insert()

        # ── 4. Chat — should return a relevant timestamp ──
        mock_answer = {
            "answer": "The speaker says 'tell me about yourself' at 3 seconds.",
            "sources": [{"text": "Tell me about yourself.", "start_time": 3.0, "end_time": 8.0}],
            "relevant_timestamp": 3.0,
        }
        with patch("app.api.routes.chat.chat_service") as mock_cs:
            mock_cs.answer_question = AsyncMock(return_value=mock_answer)
            resp = await async_client.post(
                "/api/v1/chat/",
                json={
                    "document_id": doc_id,
                    "question": "When does the speaker ask about yourself?",
                    "chat_history": [],
                },
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["relevant_timestamp"] == 3.0

    async def test_cross_user_isolation(self, async_client: AsyncClient):
        """User A cannot access User B's documents."""
        # Register User A
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "usera@example.com", "password": "password_a",
        })
        token_a = resp.json()["access_token"]

        # Register User B
        resp = await async_client.post("/api/v1/auth/register", json={
            "email": "userb@example.com", "password": "password_b",
        })
        token_b = resp.json()["access_token"]

        # User A uploads
        with patch("app.services.file_service.magic.from_buffer", return_value="application/pdf"):
            with patch("app.api.routes.upload.process_document"):
                resp = await async_client.post(
                    "/api/v1/upload/",
                    files={"file": ("secret.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
                    headers={"Authorization": f"Bearer {token_a}"},
                )
        doc_id = resp.json()["document_id"]

        # User B tries to access User A's document
        resp = await async_client.get(
            f"/api/v1/upload/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404  # Not found for this user

        # User B tries to delete User A's document
        resp = await async_client.delete(
            f"/api/v1/upload/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404
