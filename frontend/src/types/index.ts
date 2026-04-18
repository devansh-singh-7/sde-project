// ─── Auth ────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface LoginPayload {
  username: string; // OAuth2 form uses "username"
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
}

// ─── Documents ───────────────────────────────────
export type FileType = 'PDF' | 'AUDIO' | 'VIDEO';
export type DocumentStatus = 'PROCESSING' | 'READY' | 'ERROR';

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  file_type: FileType;
  file_path: string;
  transcript_text: string | null;
  summary: string | null;
  vector_store_path: string | null;
  created_at: string;
  status: DocumentStatus;
}

export interface TranscriptSegment {
  id: string;
  document_id: string;
  start_time: number;
  end_time: number;
  text: string;
  topics: string[];
}

export interface DocumentDetail {
  document: Document;
  transcript_segments: TranscriptSegment[];
}

export interface UploadResponse {
  message: string;
  document_id: string;
  file_details: {
    file_path: string;
    filename: string;
    original_filename: string;
    size_bytes: number;
    mime_type: string;
  };
}

// ─── Chat ────────────────────────────────────────
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  relevant_timestamp?: number | null;
}

export interface ChatSource {
  text: string;
  start_time: number | null;
  end_time: number | null;
}

export interface ChatRequest {
  document_id: string;
  question: string;
  chat_history: { role: string; content: string }[];
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  relevant_timestamp: number | null;
}

export interface SummaryResponse {
  summary: string;
}
