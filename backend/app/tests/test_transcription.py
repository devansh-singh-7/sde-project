import pytest
import os
import struct
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock

from app.models.document import Document, FileType, DocumentStatus
from app.models.transcript import TranscriptSegment
from app.services.transcription_service import TranscriptionService, process_document
from app.core.config import settings


@pytest.mark.asyncio
class TestPdfExtraction:
    async def test_extract_text_from_pdf(self, tmp_path):
        """Test pdfplumber extraction with a real (tiny) PDF."""
        service = TranscriptionService()

        # Create a minimal PDF with pdfplumber-readable text
        pdf_path = str(tmp_path / "test.pdf")

        # Use a mock since creating a valid PDF programmatically is complex
        with patch("app.services.transcription_service.pdfplumber") as mock_plumber:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Page one content here."
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [mock_page]
            mock_plumber.open.return_value = mock_pdf

            result = await service._process_pdf(pdf_path)

        assert result["full_text"] == "Page one content here."
        assert len(result["segments"]) == 1
        assert result["segments"][0]["text"] == "Page one content here."
        assert result["segments"][0]["start"] == 1.0
        assert result["segments"][0]["end"] == 1.0

    async def test_extract_multi_page_pdf(self, tmp_path):
        service = TranscriptionService()
        pdf_path = str(tmp_path / "multi.pdf")

        with patch("app.services.transcription_service.pdfplumber") as mock_plumber:
            pages = []
            for i in range(3):
                page = MagicMock()
                page.extract_text.return_value = f"Content of page {i + 1}"
                pages.append(page)

            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = pages
            mock_plumber.open.return_value = mock_pdf

            result = await service._process_pdf(pdf_path)

        assert len(result["segments"]) == 3
        assert result["duration"] == 3.0
        assert "page 2" in result["full_text"]

    async def test_extract_empty_pdf_page(self, tmp_path):
        service = TranscriptionService()
        pdf_path = str(tmp_path / "empty.pdf")

        with patch("app.services.transcription_service.pdfplumber") as mock_plumber:
            page = MagicMock()
            page.extract_text.return_value = None  # empty page
            mock_pdf = MagicMock()
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)
            mock_pdf.pages = [page]
            mock_plumber.open.return_value = mock_pdf

            result = await service._process_pdf(pdf_path)

        assert result["full_text"] == ""
        assert len(result["segments"]) == 0


@pytest.mark.asyncio
class TestAudioTranscription:
    async def test_transcribe_small_audio(self, mock_whisper, tmp_path):
        """Audio under 25MB should go straight to Whisper."""
        service = TranscriptionService()

        audio_path = str(tmp_path / "small.wav")
        with open(audio_path, "wb") as f:
            f.write(b"\x00" * 1000)  # small file

        with patch("os.path.getsize", return_value=1000):
            with patch("app.services.transcription_service.AudioSegment") as mock_audio:
                mock_seg = MagicMock()
                mock_seg.__len__ = MagicMock(return_value=5000)  # 5 seconds
                mock_audio.from_file.return_value = mock_seg

                result = await service._process_audio_video(audio_path)

        assert result["full_text"] == "Hello, this is a test transcription."
        assert result["language"] == "en"
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][1]["end"] == 5.0

    async def test_transcribe_large_audio_splits(self, mock_whisper, tmp_path):
        """Audio over 25MB should be split into chunks."""
        service = TranscriptionService()

        audio_path = str(tmp_path / "large.wav")
        with open(audio_path, "wb") as f:
            f.write(b"\x00" * 1000)

        with patch("os.path.getsize", return_value=30 * 1024 * 1024):  # 30MB
            with patch("app.services.transcription_service.AudioSegment") as mock_audio:
                mock_seg = MagicMock()
                mock_seg.__len__ = MagicMock(return_value=15 * 60 * 1000)  # 15 minutes
                mock_seg.__getitem__ = MagicMock(return_value=mock_seg)
                
                # Mock export to actually dump an empty file so _transcribe_audio_chunk can read it
                def mock_export_func(out_file, format=None):
                    with open(out_file, "wb") as f:
                        f.write(b"fake audio data")
                mock_seg.export.side_effect = mock_export_func

                mock_audio.from_file.return_value = mock_seg

                with patch("os.path.exists", return_value=True):
                    with patch("os.remove"):
                        result = await service._process_audio_video(audio_path)

        assert "Hello" in result["full_text"]
        assert result["language"] == "en"

    async def test_transcription_error_handling(self, tmp_path):
        """Test that errors are properly caught."""
        service = TranscriptionService()
        audio_path = str(tmp_path / "bad.wav")
        with open(audio_path, "wb") as f:
            f.write(b"\x00" * 10)

        with patch("os.path.getsize", return_value=100):
            with patch("app.services.transcription_service.AudioSegment") as mock_audio:
                mock_audio.from_file.side_effect = Exception("Corrupt file")
                with patch.object(service, "_transcribe_audio_chunk", new_callable=AsyncMock) as mock_chunk:
                    mock_chunk.side_effect = Exception("Whisper failed")

                    with pytest.raises(Exception, match="Whisper failed"):
                        await service._process_audio_video(audio_path)


@pytest.mark.asyncio
class TestProcessDocument:
    async def test_process_document_pdf_success(self, test_user):
        user = test_user["user"]
        doc = Document(
            user_id=user.to_ref(),
            filename="process_test.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/process_test.pdf",
            status=DocumentStatus.PROCESSING,
        )
        await doc.insert()

        mock_result = {
            "full_text": "Processed text content",
            "segments": [{"start": 1.0, "end": 1.0, "text": "Processed text content"}],
            "language": "en",
            "duration": 1.0,
        }

        with patch("app.services.transcription_service.transcription_service") as mock_ts:
            mock_ts.transcribe = AsyncMock(return_value=mock_result)
            with patch("app.services.transcription_service.vector_store") as mock_vs:
                mock_vs.build_vector_store = AsyncMock()
                await process_document(doc.id)

        updated = await Document.find_one(Document.id == doc.id)
        assert updated.status == DocumentStatus.READY
        assert updated.transcript_text == "Processed text content"

        segments = await TranscriptSegment.find_all().to_list()
        assert len(segments) == 1

    async def test_process_document_error_sets_status(self, test_user):
        user = test_user["user"]
        doc = Document(
            user_id=user.to_ref(),
            filename="error_test.pdf",
            file_type=FileType.PDF,
            file_path="/tmp/error_test.pdf",
            status=DocumentStatus.PROCESSING,
        )
        await doc.insert()

        with patch("app.services.transcription_service.transcription_service") as mock_ts:
            mock_ts.transcribe = AsyncMock(side_effect=Exception("Processing blew up"))
            await process_document(doc.id)

        updated = await Document.find_one(Document.id == doc.id)
        assert updated.status == DocumentStatus.ERROR

    async def test_process_nonexistent_document(self):
        # Should silently return without error
        await process_document(uuid4())
