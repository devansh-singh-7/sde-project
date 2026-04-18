import os
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
import redis.asyncio as aioredis

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangchainDocument
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.core.config import settings
from app.models.document import Document
from app.models.transcript import TranscriptSegment

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ─── QA prompt template ──────────────────────────────
QA_TEMPLATE = """Answer the user's question based strictly on the provided context.
If the context doesn't contain the answer, say so honestly.

Context:
{context}

Question: {question}

Answer:"""

QA_PROMPT = ChatPromptTemplate.from_template(QA_TEMPLATE)

SUMMARIZE_TEMPLATE = """Write a concise summary of the following text.
Capture the key points, main arguments, and conclusions.

Text:
{text}

Summary:"""

SUMMARIZE_PROMPT = ChatPromptTemplate.from_template(SUMMARIZE_TEMPLATE)


class VectorStoreService:
    def __init__(self):
        if settings.GEMINI_API_KEY == "dummy_gemini_api_key":
            from langchain_community.embeddings.fake import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=768)
        else:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=settings.GEMINI_API_KEY,
            )
        self.index_dir = os.path.join(settings.UPLOAD_DIR, "vector_indices")
        os.makedirs(self.index_dir, exist_ok=True)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

    def _get_index_path(self, document_id: str) -> str:
        return os.path.join(self.index_dir, f"{document_id}.faiss")

    async def build_vector_store(self, document_id: str, text: str, segments: List[TranscriptSegment]):
        logger.info(f"Building FAISS vector store for document: {document_id}")

        docs = []
        text_chunks = self.text_splitter.split_text(text)

        if segments:
            for chunk in text_chunks:
                start_time = None
                end_time = None
                for seg in segments:
                    if seg.text[:20] in chunk:
                        start_time = seg.start_time
                        if start_time is not None:
                            break
                for seg in reversed(segments):
                    if seg.text[-20:] in chunk:
                        end_time = seg.end_time
                        if end_time is not None:
                            break
                docs.append(LangchainDocument(page_content=chunk, metadata={"start_time": start_time, "end_time": end_time}))
        else:
            for chunk in text_chunks:
                docs.append(LangchainDocument(page_content=chunk, metadata={"start_time": None, "end_time": None}))

        if not docs:
            logger.warning(f"No texts generated for indexing document {document_id}")
            return

        faiss_store = FAISS.from_documents(docs, self.embeddings)
        index_path = self._get_index_path(document_id)
        faiss_store.save_local(index_path)
        logger.info(f"Saved FAISS index to {index_path}")

    def load_vector_store(self, document_id: str) -> FAISS:
        index_path = self._get_index_path(document_id)
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"No vector store found at {index_path}")
        return FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)

    def similarity_search(self, document_id: str, query: str, k: int = 5) -> List[LangchainDocument]:
        store = self.load_vector_store(document_id)
        return store.similarity_search(query, k=k)

vector_store = VectorStoreService()


class ChatService:
    def __init__(self):
        if settings.GEMINI_API_KEY == "dummy_gemini_api_key" or not settings.GEMINI_API_KEY:
            from langchain_community.chat_models.fake import FakeListChatModel
            self.llm = FakeListChatModel(responses=["This is a mock response because GEMINI_API_KEY is dummy."])
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.2,
            )
        # Redis is optional — lazy connect so startup doesn't fail if unavailable
        self._redis_url = settings.REDIS_URL
        self._redis_client: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> Optional[aioredis.Redis]:
        if self._redis_client is None:
            try:
                self._redis_client = aioredis.from_url(self._redis_url, decode_responses=True)
                await self._redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis unavailable, caching disabled: {e}")
                self._redis_client = None
        return self._redis_client

    def _format_docs(self, docs: List[LangchainDocument]) -> str:
        return "\n\n".join(doc.page_content for doc in docs)

    async def answer_question(self, document_id: str, question: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        logger.info(f"Answering question for document {document_id}")
        try:
            store = vector_store.load_vector_store(document_id)
        except Exception as e:
            logger.error(f"Vector store load failed: {e}")
            return {"answer": "Document index not found.", "sources": [], "relevant_timestamp": None}

        retriever = store.as_retriever(search_kwargs={"k": 5})

        # Retrieve source documents
        source_docs = retriever.invoke(question)

        # Build LCEL chain
        chain = (
            {"context": lambda x: self._format_docs(source_docs), "question": RunnablePassthrough()}
            | QA_PROMPT
            | self.llm
            | StrOutputParser()
        )

        answer = await chain.ainvoke(question)

        sources = []
        relevant_timestamp = None
        for doc in source_docs:
            sources.append({
                "text": doc.page_content,
                "start_time": doc.metadata.get("start_time"),
                "end_time": doc.metadata.get("end_time")
            })
            if relevant_timestamp is None and doc.metadata.get("start_time") is not None:
                relevant_timestamp = doc.metadata.get("start_time")

        return {
            "answer": answer,
            "sources": sources,
            "relevant_timestamp": relevant_timestamp
        }

    async def summarize_document(self, document_id: str) -> str:
        cache_key = f"summary:{document_id}"

        redis = await self._get_redis()
        if redis:
            cached_summary = await redis.get(cache_key)
            if cached_summary:
                logger.info("Returning cached summary")
                return cached_summary

        logger.info(f"Generating summary for document {document_id}")
        doc = await Document.find_one(Document.id == document_id)
        if not doc or not doc.transcript_text:
            return "Transcript not available."

        # Chunk and summarize each chunk, then combine
        chunks = vector_store.text_splitter.split_text(doc.transcript_text)

        chain = SUMMARIZE_PROMPT | self.llm | StrOutputParser()

        try:
            # Summarize chunks then combine
            if len(chunks) <= 3:
                combined_text = "\n\n".join(chunks)
                summary = await chain.ainvoke({"text": combined_text})
            else:
                # Map-reduce: summarize each chunk, then summarize summaries
                chunk_summaries = []
                for chunk in chunks:
                    s = await chain.ainvoke({"text": chunk})
                    chunk_summaries.append(s)
                summary = await chain.ainvoke({"text": "\n\n".join(chunk_summaries)})

            if redis:
                await redis.setex(cache_key, 3600, summary)
            return summary
        except Exception as e:
            logger.error(f"Failed to summarize document: {e}")
            return "Summarization failed."

    async def stream_answer(self, document_id: str, question: str, chat_history: List[Dict[str, str]] = None) -> AsyncGenerator[str, None]:
        store = vector_store.load_vector_store(document_id)
        retriever = store.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])

        chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | QA_PROMPT
            | ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.2,
                streaming=True,
            )
            | StrOutputParser()
        )

        async for chunk in chain.astream(question):
            yield chunk

chat_service = ChatService()
