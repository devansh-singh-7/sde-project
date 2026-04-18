import { useState, useRef, useEffect, useCallback, type FormEvent, type KeyboardEvent } from 'react';
import { Send, Bot, User, Play, Trash2, Sparkles } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import type { ChatMessage, ChatResponse } from '../types';
import { chatApi } from '../api/chat';

interface Props {
  documentId: string;
  onTimestampClick?: (seconds: number) => void;
}

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

const SUGGESTIONS = [
  "What is this document about?",
  "Summarize the key points",
  "What are the main conclusions?",
];

export default function ChatWindow({ documentId, onTimestampClick }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isWaitingFirstToken, setIsWaitingFirstToken] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const token = useAuthStore((s) => s.token);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  // Reset messages when document changes
  useEffect(() => {
    setMessages([]);
    setInput('');
    setIsStreaming(false);
    setIsWaitingFirstToken(false);
    eventSourceRef.current?.close();
  }, [documentId]);

  const sendMessageWithStream = useCallback(
    async (question: string) => {
      const userMsg: ChatMessage = { role: 'user', content: question };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
      setIsWaitingFirstToken(true);

      const assistantMsg: ChatMessage = { role: 'assistant', content: '', sources: [], relevant_timestamp: null };
      setMessages((prev) => [...prev, assistantMsg]);

      eventSourceRef.current?.close();

      const url = `/api/v1/chat/stream?document_id=${encodeURIComponent(documentId)}&question=${encodeURIComponent(question)}&token=${encodeURIComponent(token || '')}`;

      try {
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) throw new Error(`Stream failed: ${res.status}`);

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let accumulated = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const tokenText = line.slice(6);
              accumulated += tokenText;
              setIsWaitingFirstToken(false);

              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                updated[updated.length - 1] = { ...last, content: accumulated };
                return updated;
              });
            }
          }
        }
      } catch {
        try {
          const history = messages.map((m) => ({ role: m.role, content: m.content }));
          const res: ChatResponse = await chatApi({
            document_id: documentId,
            question,
            chat_history: history,
          });

          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: 'assistant',
              content: res.answer,
              sources: res.sources,
              relevant_timestamp: res.relevant_timestamp,
            };
            return updated;
          });
        } catch {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: 'Sorry, something went wrong. Please try again.',
            };
            return updated;
          });
        }
      } finally {
        setIsStreaming(false);
        setIsWaitingFirstToken(false);
      }
    },
    [documentId, messages, token]
  );

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || isStreaming || !documentId || documentId === 'undefined') return;
    setInput('');
    sendMessageWithStream(q);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  };

  const clearChat = () => {
    setMessages([]);
    eventSourceRef.current?.close();
    setIsStreaming(false);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* ─── Header ─── */}
      <div className="px-5 py-3 border-b border-glass-border flex items-center justify-between shrink-0">
        <h3 className="font-semibold text-sm flex items-center gap-2 text-text-muted">
          <Sparkles size={15} className="text-primary-light" />
          Ask about this document
        </h3>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1.5 text-xs text-text-faint hover:text-danger transition-colors px-2 py-1 rounded-lg hover:bg-danger/5"
          >
            <Trash2 size={12} />
            Clear
          </button>
        )}
      </div>

      {/* ─── Messages ─── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3"
              style={{ background: 'rgba(99,102,241,0.08)' }}
            >
              <Bot size={24} className="text-text-faint" />
            </div>
            <p className="text-sm font-medium text-text-muted">How can I help?</p>
            <p className="text-xs text-text-faint mt-1 mb-4">Ask anything about the document</p>

            {/* Suggestions */}
            <div className="flex flex-col gap-2 max-w-xs mx-auto">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(''); sendMessageWithStream(s); }}
                  className="text-xs text-left px-3 py-2 rounded-lg transition-all duration-200 text-text-muted hover:text-primary-light"
                  style={{
                    background: 'rgba(99,102,241,0.06)',
                    border: '1px solid rgba(99,102,241,0.1)',
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 animate-fade-slide-up ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {/* Avatar */}
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: 'rgba(99,102,241,0.12)' }}
              >
                <Bot size={14} className="text-primary-light" />
              </div>
            )}

            <div className="max-w-[80%] space-y-1.5">
              {/* Bubble */}
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'rounded-br-md text-white'
                    : 'rounded-bl-md text-text'
                }`}
                style={msg.role === 'user' ? {
                  background: 'linear-gradient(135deg, #6366F1, #4F46E5)',
                } : {
                  background: 'rgba(30, 41, 59, 0.4)',
                  border: '1px solid rgba(148, 163, 184, 0.08)',
                }}
              >
                <p className="whitespace-pre-wrap">
                  {msg.content}
                  {isStreaming && i === messages.length - 1 && msg.role === 'assistant' && (
                    <span className="inline-block w-1.5 h-4 ml-0.5 bg-primary-light rounded-sm animate-pulse" />
                  )}
                </p>
              </div>

              {/* Timestamp jump button */}
              {msg.role === 'assistant' && msg.relevant_timestamp != null && msg.relevant_timestamp > 0 && (
                <button
                  onClick={() => onTimestampClick?.(msg.relevant_timestamp!)}
                  className="flex items-center gap-1.5 text-xs font-medium text-primary-light hover:text-accent-cyan transition-colors pl-1 group"
                >
                  <Play size={11} className="group-hover:scale-110 transition-transform" />
                  Jump to {formatTimestamp(msg.relevant_timestamp)}
                </button>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: 'linear-gradient(135deg, #6366F1, #22D3EE)' }}
              >
                <User size={14} className="text-white" />
              </div>
            )}
          </div>
        ))}

        {/* Thinking indicator */}
        {isWaitingFirstToken && (
          <div className="flex gap-3 animate-fade-slide-up">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: 'rgba(99,102,241,0.12)' }}
            >
              <Bot size={14} className="text-primary-light" />
            </div>
            <div className="flex items-center gap-1.5 pt-2">
              <div className="w-2 h-2 bg-primary-light rounded-full animate-bounce-dot" />
              <div className="w-2 h-2 bg-primary-light rounded-full animate-bounce-dot animate-delay-200" />
              <div className="w-2 h-2 bg-primary-light rounded-full animate-bounce-dot animate-delay-400" />
            </div>
          </div>
        )}
      </div>

      {/* ─── Input ─── */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-glass-border shrink-0">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question…"
            rows={1}
            className="input-glass flex-1 resize-none max-h-28"
            style={{ minHeight: '40px' }}
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="p-2.5 rounded-xl transition-all duration-200 disabled:opacity-30 shrink-0"
            style={{
              background: input.trim() && !isStreaming
                ? 'linear-gradient(135deg, #6366F1, #4F46E5)'
                : 'rgba(51, 65, 85, 0.3)',
            }}
          >
            <Send size={16} className="text-white" />
          </button>
        </div>
      </form>
    </div>
  );
}
