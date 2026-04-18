from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks, Request
from uuid import UUID
from typing import List
import os

from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document, FileType, DocumentStatus
from app.models.transcript import TranscriptSegment
from app.services.file_service import file_service
from app.services.transcription_service import process_document
from app.core.rate_limit import limiter

router = APIRouter()

@router.post("/", response_model=dict)
@limiter.limit("30/minute")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # 1. Validate File structure via Magic and Save
    file_info = await file_service.validate_and_save_file(file)
    
    # 2. Classify into document models
    mime = file_info["mime_type"]
    if "pdf" in mime:
        file_type = FileType.PDF
    elif "audio" in mime:
        file_type = FileType.AUDIO
    else:
        file_type = FileType.VIDEO
        
    # 3. Create document record in database
    doc = Document(
        user_id=current_user.to_ref(),
        filename=file_info["original_filename"],
        file_type=file_type,
        file_path=file_info["file_path"],
        status=DocumentStatus.PROCESSING
    )
    await doc.insert()
    
    # 4. Enqueue post-processing features
    background_tasks.add_task(process_document, doc.id)
    
    return {
        "message": "File uploaded successfully",
        "document_id": doc.id,
        "file_details": file_info
    }

@router.get("/documents")
@limiter.limit("30/minute")
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    docs = await Document.find(Document.user_id == current_user.to_ref()).skip(skip).limit(limit).to_list()
    return docs

@router.get("/documents/{document_id}")
@limiter.limit("30/minute")
async def get_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    doc = await Document.find_one(
        Document.id == document_id, 
        Document.user_id == current_user.to_ref()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    segments = await TranscriptSegment.find(TranscriptSegment.document_id == doc.to_ref()).to_list()
    
    return {
        "document": doc,
        "transcript_segments": segments
    }

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    doc = await Document.find_one(
        Document.id == document_id, 
        Document.user_id == current_user.to_ref()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    # Delete binary file from operating system
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        
    # Deep cascade database deletions
    await TranscriptSegment.find(TranscriptSegment.document_id == doc.to_ref()).delete()
    await doc.delete()
    
    return None
