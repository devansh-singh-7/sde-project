import pytest
import io
from unittest.mock import patch
from httpx import AsyncClient

from app.models.document import Document, FileType, DocumentStatus
from app.models.transcript import TranscriptSegment


@pytest.mark.asyncio
class TestUploadEndpoint:
    async def test_upload_pdf_success(
        self, async_client: AsyncClient, test_user, sample_pdf_file, mock_magic_pdf
    ):
        name, content, content_type = sample_pdf_file
        # Patch background task so it doesn't actually run transcription
        with patch("app.api.routes.upload.process_document"):
            resp = await async_client.post(
                "/api/v1/upload/",
                files={"file": (name, content, content_type)},
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "File uploaded successfully"
        assert "document_id" in data

    async def test_upload_audio_success(
        self, async_client: AsyncClient, test_user, sample_audio_file, mock_magic_audio
    ):
        name, content, content_type = sample_audio_file
        with patch("app.api.routes.upload.process_document"):
            resp = await async_client.post(
                "/api/v1/upload/",
                files={"file": (name, content, content_type)},
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )
        assert resp.status_code == 200

    async def test_upload_unsupported_type(
        self, async_client: AsyncClient, test_user, mock_magic_unsupported
    ):
        resp = await async_client.post(
            "/api/v1/upload/",
            files={"file": ("test.exe", io.BytesIO(b"\x00" * 100), "application/x-executable")},
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 415

    async def test_upload_unauthenticated(self, async_client: AsyncClient, sample_pdf_file):
        name, content, content_type = sample_pdf_file
        resp = await async_client.post(
            "/api/v1/upload/",
            files={"file": (name, content, content_type)},
        )
        assert resp.status_code == 401

    async def test_upload_no_file(self, async_client: AsyncClient, test_user):
        resp = await async_client.post(
            "/api/v1/upload/",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestDocumentsList:
    async def test_list_documents_empty(self, async_client: AsyncClient, test_user):
        resp = await async_client.get(
            "/api/v1/upload/documents",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_documents_with_data(self, async_client: AsyncClient, test_user):
        user = test_user["user"]
        doc = Document(
            user_id=user.to_ref(),
            filename="report.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/report.pdf",
            status=DocumentStatus.READY,
        )
        await doc.insert()

        resp = await async_client.get(
            "/api/v1/upload/documents",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["filename"] == "report.pdf"

    async def test_list_documents_pagination(self, async_client: AsyncClient, test_user):
        user = test_user["user"]
        for i in range(5):
            doc = Document(
                user_id=user.to_ref(),
                filename=f"doc_{i}.pdf",
                file_type=FileType.PDF,
                file_path=f"/tmp/doc_{i}.pdf",
                status=DocumentStatus.READY,
            )
            await doc.insert()

        resp = await async_client.get(
            "/api/v1/upload/documents?skip=0&limit=2",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_list_documents_unauthenticated(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/upload/documents")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestDocumentDetail:
    async def test_get_document_success(self, async_client: AsyncClient, test_user):
        user = test_user["user"]
        doc = Document(
            user_id=user.to_ref(),
            filename="detail.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/detail.pdf",
            status=DocumentStatus.READY,
        )
        await doc.insert()

        resp = await async_client.get(
            f"/api/v1/upload/documents/{doc.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["document"]["filename"] == "detail.pdf"

    async def test_get_document_not_found(self, async_client: AsyncClient, test_user):
        from uuid import uuid4

        resp = await async_client.get(
            f"/api/v1/upload/documents/{uuid4()}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 404

    async def test_get_document_unauthenticated(self, async_client: AsyncClient):
        from uuid import uuid4

        resp = await async_client.get(f"/api/v1/upload/documents/{uuid4()}")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestDocumentDelete:
    async def test_delete_document_success(self, async_client: AsyncClient, test_user):
        user = test_user["user"]
        doc = Document(
            user_id=user.to_ref(),
            filename="todelete.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/nonexistent.pdf",  # file doesn't exist on disk, that's ok
            status=DocumentStatus.READY,
        )
        await doc.insert()

        resp = await async_client.delete(
            f"/api/v1/upload/documents/{doc.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 204

        # Verify it's gone
        deleted = await Document.find_one(Document.id == doc.id)
        assert deleted is None

    async def test_delete_cascades_segments(self, async_client: AsyncClient, test_user):
        user = test_user["user"]
        doc = Document(
            user_id=user.to_ref(),
            filename="cascade.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/cascade.pdf",
            status=DocumentStatus.READY,
        )
        await doc.insert()

        seg = TranscriptSegment(
            document_id=doc.to_ref(),
            start_time=0.0,
            end_time=5.0,
            text="Test segment",
        )
        await seg.insert()

        resp = await async_client.delete(
            f"/api/v1/upload/documents/{doc.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 204

        remaining = await TranscriptSegment.find_all().to_list()
        assert len(remaining) == 0

    async def test_delete_document_not_found(self, async_client: AsyncClient, test_user):
        from uuid import uuid4

        resp = await async_client.delete(
            f"/api/v1/upload/documents/{uuid4()}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 404
