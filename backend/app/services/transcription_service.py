import os
import math
from typing import Dict, Any, List, Optional
from uuid import UUID

import pdfplumber
from pydub import AudioSegment
from openai import AsyncOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from app.core.config import settings
from app.models.document import Document, FileType, DocumentStatus
from app.models.transcript import TranscriptSegment
from app.services.ai_service import vector_store

# Initialize AsyncOpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class TranscriptionService:
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    async def _transcribe_audio_chunk(self, chunk_path: str) -> Dict[str, Any]:
        """Wrapper for OpenAI API with retry logic"""
        with open(chunk_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return dict(response)

    async def _process_audio_video(self, file_path: str) -> Dict[str, Any]:
        file_size = os.path.getsize(file_path)
        MAX_BYTES = 25 * 1024 * 1024 # 25MB limit for whisper
        
        full_text = ""
        segments = []
        language = "unknown"
        duration = 0.0

        if file_size > MAX_BYTES:
            # 4. Split audio using pydub
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0
            
            # Simple chunking: 10 minutes chunk length (usually safe under 25MB for MP3)
            chunk_length_ms = 10 * 60 * 1000
            chunks = math.ceil(len(audio) / chunk_length_ms)
            
            time_offset = 0.0
            for i in range(chunks):
                start_ms = i * chunk_length_ms
                end_ms = min((i + 1) * chunk_length_ms, len(audio))
                chunk = audio[start_ms:end_ms]
                
                chunk_path = f"{file_path}.chunk{i}.mp3"
                chunk.export(chunk_path, format="mp3")
                
                try:
                    res = await self._transcribe_audio_chunk(chunk_path)
                    
                    full_text += res.get("text", "") + " "
                    if i == 0:
                        language = res.get("language", "unknown")
                    
                    for seg in res.get("segments", []):
                        segments.append({
                            "start": seg.get("start", 0.0) + time_offset,
                            "end": seg.get("end", 0.0) + time_offset,
                            "text": seg.get("text", "")
                        })
                finally:
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                        
                time_offset += (end_ms - start_ms) / 1000.0
        else:
            # Directly process under 25MB
            try:
                audio = AudioSegment.from_file(file_path)
                duration = len(audio) / 1000.0
            except:
                duration = 0.0 # Fallback in case of corruption
                
            res = await self._transcribe_audio_chunk(file_path)
            full_text = res.get("text", "")
            language = res.get("language", "unknown")
            
            for seg in res.get("segments", []):
                segments.append({
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "text": seg.get("text", "")
                })

        return {
            "full_text": full_text.strip(),
            "segments": segments,
            "language": language,
            "duration": duration
        }

    async def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF using pdfplumber."""
        full_text = ""
        segments = []
        
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
                    # Maps pages to 'start' / 'end' logic broadly
                    segments.append({
                        "start": float(i + 1),
                        "end": float(i + 1),
                        "text": text.strip()
                    })
                    
        return {
            "full_text": full_text.strip(),
            "segments": segments,
            "language": "unknown",
            "duration": float(len(segments)) # represents page count
        }

    async def transcribe(self, file_path: str, file_type: FileType) -> Dict[str, Any]:
        if file_type == FileType.PDF:
            return await self._process_pdf(file_path)
        else:
            return await self._process_audio_video(file_path)
            
transcription_service = TranscriptionService()

async def process_document(document_id: UUID):
    try:
        # Fetch document
        doc = await Document.find_one(Document.id == document_id)
        if not doc:
            return

        # Transcribe the file
        result = await transcription_service.transcribe(doc.file_path, doc.file_type)
        
        # Save full text
        doc.transcript_text = result["full_text"]
        await doc.save()

        # Save segments to TranscriptSegment
        db_segments = []
        for seg in result["segments"]:
            transcript_segment = TranscriptSegment(
                document_id=doc.to_ref(),
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],
                topics=[]
            )
            db_segments.append(transcript_segment)
            
        if db_segments:
            await TranscriptSegment.insert_many(db_segments)

        # Call vector_store_service to index
        try:
            await vector_store.build_vector_store(doc.id, result["full_text"], db_segments)
        except Exception as e:
            print(f"Vector indexing non-fatal error: {e}")
            pass

        # Update Document status to READY
        doc.status = DocumentStatus.READY
        await doc.save()
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        doc = await Document.find_one(Document.id == document_id)
        if doc:
            doc.status = DocumentStatus.ERROR
            await doc.save()
