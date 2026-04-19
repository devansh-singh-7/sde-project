import client, { apiBaseUrl } from './client';
import type { ChatRequest, ChatResponse, SummaryResponse } from '../types';

export const chatApi = async (payload: ChatRequest): Promise<ChatResponse> => {
  const { data } = await client.post<ChatResponse>('/chat/', payload);
  return data;
};

export const summarizeApi = async (documentId: string): Promise<SummaryResponse> => {
  const { data } = await client.post<SummaryResponse>(`/chat/summarize/${documentId}`);
  return data;
};

/**
 * SSE stream for chat. Returns a ReadableStream via fetch (not axios).
 */
export const streamChatApi = async (
  documentId: string,
  question: string,
  token: string
): Promise<ReadableStreamDefaultReader<Uint8Array>> => {
  const url = `${apiBaseUrl}/chat/stream?document_id=${encodeURIComponent(documentId)}&question=${encodeURIComponent(question)}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Stream request failed');
  return res.body!.getReader();
};
