import client from './client';
import type { Document, DocumentDetail, UploadResponse, SummaryResponse } from '../types';

export const uploadDocument = async (
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadResponse> => {
  const form = new FormData();
  form.append('file', file);
  const { data } = await client.post<UploadResponse>('/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return data;
};

export const getDocuments = async (skip = 0, limit = 20): Promise<Document[]> => {
  const { data } = await client.get<any[]>('/upload/documents', {
    params: { skip, limit },
  });
  return data.map(d => ({ ...d, id: d.id || d._id }));
};

export const getDocument = async (id: string): Promise<DocumentDetail> => {
  const { data } = await client.get<any>(`/upload/documents/${id}`);
  if (data?.document) {
    data.document.id = data.document.id || data.document._id;
  }
  return data;
};

export const deleteDocument = async (id: string): Promise<void> => {
  await client.delete(`/upload/documents/${id}`);
};

export const summarizeDocument = async (id: string): Promise<SummaryResponse> => {
  const { data } = await client.post<SummaryResponse>(`/chat/summarize/${id}`);
  return data;
};
