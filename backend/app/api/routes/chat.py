from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document
from app.services.ai_service import chat_service
from app.core.rate_limit import limiter

router = APIRouter()

class ChatRequest(BaseModel):
    document_id: str
    question: str
    chat_history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    relevant_timestamp: Optional[float] = None

class SummarizeResponse(BaseModel):
    summary: str

async def check_doc_access(document_id: str, current_user: User):
    doc = await Document.find_one(Document.id == document_id, Document.user_id == current_user.to_ref())
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or access denied")
    return doc

@router.post("/", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    await check_doc_access(payload.document_id, current_user)
    
    result = await chat_service.answer_question(
        payload.document_id,
        payload.question,
        payload.chat_history
    )
    return result

@router.get("/stream")
@limiter.limit("10/minute")
async def stream_chat(
    request: Request,
    document_id: str,
    question: str,
    current_user: User = Depends(get_current_user)
):
    await check_doc_access(document_id, current_user)
    
    async def event_generator():
        async for chunk in chat_service.stream_answer(document_id, question):
            # Format SSE manually here
            yield f"data: {chunk}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/summarize/{document_id}", response_model=SummarizeResponse)
@limiter.limit("10/minute")
async def summarize(
    request: Request,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    await check_doc_access(document_id, current_user)
    
    summary = await chat_service.summarize_document(document_id)
    return {"summary": summary}
