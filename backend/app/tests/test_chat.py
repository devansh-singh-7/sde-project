import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient

from app.models.document import Document, FileType, DocumentStatus


@pytest.mark.asyncio
class TestChatEndpoint:
    async def _create_ready_doc(self, user):
        doc = Document(
            user_id=user.to_ref(),
            filename="chat_test.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/chat.pdf",
            transcript_text="This is test content for chatting.",
            status=DocumentStatus.READY,
        )
        await doc.insert()
        return doc

    async def test_chat_success(self, async_client: AsyncClient, test_user):
        doc = await self._create_ready_doc(test_user["user"])

        mock_result = {
            "answer": "The document discusses testing.",
            "sources": [{"text": "test content", "start_time": None, "end_time": None}],
            "relevant_timestamp": None,
        }

        with patch("app.api.routes.chat.chat_service") as mock_svc:
            mock_svc.answer_question = AsyncMock(return_value=mock_result)

            resp = await async_client.post(
                "/api/v1/chat/",
                json={
                    "document_id": str(doc.id),
                    "question": "What does this document discuss?",
                    "chat_history": [],
                },
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "The document discusses testing."
        assert len(data["sources"]) == 1

    async def test_chat_with_timestamp(self, async_client: AsyncClient, test_user):
        doc = await self._create_ready_doc(test_user["user"])

        mock_result = {
            "answer": "At 1 minute 30 seconds, the speaker says hello.",
            "sources": [{"text": "hello world", "start_time": 90.0, "end_time": 95.0}],
            "relevant_timestamp": 90.0,
        }

        with patch("app.api.routes.chat.chat_service") as mock_svc:
            mock_svc.answer_question = AsyncMock(return_value=mock_result)

            resp = await async_client.post(
                "/api/v1/chat/",
                json={
                    "document_id": str(doc.id),
                    "question": "When does the speaker say hello?",
                    "chat_history": [],
                },
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )

        assert resp.status_code == 200
        assert resp.json()["relevant_timestamp"] == 90.0

    async def test_chat_document_not_found(self, async_client: AsyncClient, test_user):
        resp = await async_client.post(
            "/api/v1/chat/",
            json={
                "document_id": str(uuid4()),
                "question": "Hello?",
                "chat_history": [],
            },
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 404

    async def test_chat_unauthenticated(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/chat/",
            json={
                "document_id": str(uuid4()),
                "question": "Hello?",
                "chat_history": [],
            },
        )
        assert resp.status_code == 401

    async def test_chat_missing_question(self, async_client: AsyncClient, test_user):
        doc = await self._create_ready_doc(test_user["user"])
        resp = await async_client.post(
            "/api/v1/chat/",
            json={"document_id": str(doc.id)},
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestStreamEndpoint:
    async def _create_ready_doc(self, user):
        doc = Document(
            user_id=user.to_ref(),
            filename="stream_test.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/stream.pdf",
            transcript_text="Streaming test content.",
            status=DocumentStatus.READY,
        )
        await doc.insert()
        return doc

    async def test_stream_returns_sse(self, async_client: AsyncClient, test_user):
        doc = await self._create_ready_doc(test_user["user"])

        async def mock_stream(*args, **kwargs):
            for token in ["Hello", " world", "!"]:
                yield token

        with patch("app.api.routes.chat.chat_service") as mock_svc:
            mock_svc.stream_answer = mock_stream

            resp = await async_client.get(
                f"/api/v1/chat/stream?document_id={doc.id}&question=Hello",
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body = resp.text
        assert "data: Hello" in body

    async def test_stream_unauthenticated(self, async_client: AsyncClient):
        resp = await async_client.get(
            f"/api/v1/chat/stream?document_id={uuid4()}&question=Hi",
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestSummarizeEndpoint:
    async def _create_ready_doc(self, user):
        doc = Document(
            user_id=user.to_ref(),
            filename="summarize_test.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/summarize.pdf",
            transcript_text="Long document content for summarization.",
            status=DocumentStatus.READY,
        )
        await doc.insert()
        return doc

    async def test_summarize_success(self, async_client: AsyncClient, test_user):
        doc = await self._create_ready_doc(test_user["user"])

        with patch("app.api.routes.chat.chat_service") as mock_svc:
            mock_svc.summarize_document = AsyncMock(return_value="This is a concise summary.")

            resp = await async_client.post(
                f"/api/v1/chat/summarize/{doc.id}",
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )

        assert resp.status_code == 200
        assert resp.json()["summary"] == "This is a concise summary."

    async def test_summarize_document_not_found(self, async_client: AsyncClient, test_user):
        resp = await async_client.post(
            f"/api/v1/chat/summarize/{uuid4()}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert resp.status_code == 404

    async def test_summarize_unauthenticated(self, async_client: AsyncClient):
        resp = await async_client.post(f"/api/v1/chat/summarize/{uuid4()}")
        assert resp.status_code == 401
