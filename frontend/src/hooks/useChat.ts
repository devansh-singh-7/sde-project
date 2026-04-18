import { useState, useCallback } from 'react';
import { chatApi, streamChatApi } from '../api/chat';
import { useAuthStore } from '../store/authStore';
import type { ChatMessage } from '../types';

export function useChat(documentId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const token = useAuthStore((s) => s.token);

  const sendMessage = useCallback(
    async (question: string) => {
      const userMsg: ChatMessage = { role: 'user', content: question };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const history = messages.map((m) => ({ role: m.role, content: m.content }));
        const res = await chatApi({
          document_id: documentId,
          question,
          chat_history: history,
        });

        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: res.answer,
          sources: res.sources,
          relevant_timestamp: res.relevant_timestamp,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'Sorry, something went wrong.' },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [documentId, messages]
  );

  const sendMessageStreaming = useCallback(
    async (question: string) => {
      const userMsg: ChatMessage = { role: 'user', content: question };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      // Add empty assistant message that we'll build up
      const assistantIdx = messages.length + 1;
      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      try {
        const reader = await streamChatApi(documentId, question, token!);
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          // Parse SSE lines
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              buffer += line.slice(6);
              setMessages((prev) => {
                const updated = [...prev];
                updated[assistantIdx] = { ...updated[assistantIdx], content: buffer };
                return updated;
              });
            }
          }
        }
      } catch {
        setMessages((prev) => {
          const updated = [...prev];
          updated[assistantIdx] = {
            ...updated[assistantIdx],
            content: updated[assistantIdx].content || 'Streaming failed.',
          };
          return updated;
        });
      } finally {
        setIsLoading(false);
      }
    },
    [documentId, messages, token]
  );

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, isLoading, sendMessage, sendMessageStreaming, clearMessages };
}
