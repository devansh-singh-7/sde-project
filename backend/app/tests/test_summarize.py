import pytest
import os
from uuid import uuid4
from unittest.mock import patch, MagicMock

from app.services.ai_service import VectorStoreService
from app.models.transcript import TranscriptSegment


@pytest.mark.asyncio
class TestBuildVectorStore:
    async def test_build_vector_store_success(self, tmp_path):
        service = VectorStoreService()
        service.index_dir = str(tmp_path)

        doc_id = uuid4()
        text = "This is a sample text for vector indexing. " * 20  # enough for chunking

        segments = [
            TranscriptSegment(
                document_id=str(doc_id),
                start_time=0.0,
                end_time=5.0,
                text="This is a sample text",
            ),
        ]

        with patch.object(service, "embeddings") as mock_emb:
            mock_emb.embed_documents = MagicMock(return_value=[[0.1] * 1536])
            mock_emb.embed_query = MagicMock(return_value=[0.1] * 1536)

            with patch("app.services.ai_service.FAISS") as mock_faiss:
                mock_store = MagicMock()
                mock_faiss.from_documents.return_value = mock_store

                await service.build_vector_store(doc_id, text, segments)

                mock_faiss.from_documents.assert_called_once()
                mock_store.save_local.assert_called_once()

    async def test_build_vector_store_empty_text(self, tmp_path):
        service = VectorStoreService()
        service.index_dir = str(tmp_path)

        doc_id = uuid4()
        # Empty text should not crash
        await service.build_vector_store(doc_id, "", [])


@pytest.mark.asyncio
class TestLoadVectorStore:
    async def test_load_nonexistent_raises(self, tmp_path):
        service = VectorStoreService()
        service.index_dir = str(tmp_path)

        with pytest.raises(FileNotFoundError):
            service.load_vector_store(uuid4())

    async def test_load_existing_store(self, tmp_path):
        service = VectorStoreService()
        service.index_dir = str(tmp_path)

        doc_id = uuid4()
        index_path = os.path.join(str(tmp_path), f"{str(doc_id)}.faiss")
        os.makedirs(index_path, exist_ok=True)

        with patch("app.services.ai_service.FAISS") as mock_faiss:
            mock_faiss.load_local.return_value = MagicMock()
            store = service.load_vector_store(doc_id)
            mock_faiss.load_local.assert_called_once()


@pytest.mark.asyncio
class TestSimilaritySearch:
    async def test_similarity_search_returns_results(self, tmp_path):
        service = VectorStoreService()
        service.index_dir = str(tmp_path)

        doc_id = uuid4()
        index_path = os.path.join(str(tmp_path), f"{str(doc_id)}.faiss")
        os.makedirs(index_path, exist_ok=True)

        mock_doc = MagicMock()
        mock_doc.page_content = "Relevant chunk"
        mock_doc.metadata = {"start_time": 10.0, "end_time": 15.0}

        with patch("app.services.ai_service.FAISS") as mock_faiss:
            mock_store = MagicMock()
            mock_store.similarity_search.return_value = [mock_doc]
            mock_faiss.load_local.return_value = mock_store

            results = service.similarity_search(doc_id, "query", k=3)

        assert len(results) == 1
        assert results[0].page_content == "Relevant chunk"
        assert results[0].metadata["start_time"] == 10.0

    async def test_similarity_search_no_index(self, tmp_path):
        service = VectorStoreService()
        service.index_dir = str(tmp_path)

        with pytest.raises(FileNotFoundError):
            service.similarity_search(uuid4(), "query")
