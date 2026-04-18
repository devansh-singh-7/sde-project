import { useState, useMemo } from 'react';
import FileUploader from '../components/FileUploader';
import DocumentList from '../components/DocumentList';
import ChatWindow from '../components/ChatWindow';
import { useQueryClient } from '@tanstack/react-query';
import { useDocuments } from '../hooks/useDocuments';
import { FileText, Cpu, CheckCircle, ChevronDown, MessageSquare, Sparkles } from 'lucide-react';
import type { Document } from '../types';

export default function Dashboard() {
  const qc = useQueryClient();
  const { data: docs } = useDocuments();
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [showDocPicker, setShowDocPicker] = useState(false);

  const readyDocs = useMemo(() => (docs || []).filter((d: Document) => d.status === 'READY'), [docs]);
  const processingDocs = useMemo(() => (docs || []).filter((d: Document) => d.status === 'PROCESSING'), [docs]);

  const selectedDoc = useMemo(
    () => readyDocs.find((d: Document) => d.id === selectedDocId) || null,
    [readyDocs, selectedDocId]
  );

  const handleUploadComplete = (_documentId: string) => {
    qc.invalidateQueries({ queryKey: ['documents'] });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            <span className="gradient-text">Dashboard</span>
          </h1>
          <p className="text-text-muted text-sm mt-1">Upload documents and start asking questions with AI</p>
        </div>
      </div>

      {/* ── Stats ── */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-card px-5 py-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.15)' }}>
            <FileText size={20} className="text-primary-light" />
          </div>
          <div>
            <p className="text-2xl font-bold">{docs?.length || 0}</p>
            <p className="text-xs text-text-muted">Total Documents</p>
          </div>
        </div>
        <div className="glass-card px-5 py-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(52,211,153,0.15)' }}>
            <CheckCircle size={20} className="text-success" />
          </div>
          <div>
            <p className="text-2xl font-bold">{readyDocs.length}</p>
            <p className="text-xs text-text-muted">Ready</p>
          </div>
        </div>
        <div className="glass-card px-5 py-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(251,191,36,0.15)' }}>
            <Cpu size={20} className="text-warning" />
          </div>
          <div>
            <p className="text-2xl font-bold">{processingDocs.length}</p>
            <p className="text-xs text-text-muted">Processing</p>
          </div>
        </div>
      </div>

      {/* ── Main Content: 2 columns ── */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Left: Upload + List */}
        <div className="xl:col-span-3 space-y-6">
          <FileUploader onUploadComplete={handleUploadComplete} />

          <div>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <FileText size={18} className="text-text-faint" />
              Your Documents
            </h2>
            <DocumentList />
          </div>
        </div>

        {/* Right: Chat Panel */}
        <div className="xl:col-span-2">
          <div className="glass-card overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 14rem)' }}>
            {/* Chat Header with Doc Picker */}
            <div className="px-5 py-4 border-b border-glass-border">
              <h3 className="font-semibold text-sm flex items-center gap-2 mb-3">
                <Sparkles size={16} className="text-primary-light" />
                AI Chat
              </h3>

              {/* Document selector */}
              <div className="relative">
                <button
                  onClick={() => setShowDocPicker(!showDocPicker)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all duration-200"
                  style={{
                    background: 'rgba(15, 23, 42, 0.5)',
                    border: '1px solid rgba(148, 163, 184, 0.12)',
                  }}
                >
                  <span className={selectedDoc ? 'text-text' : 'text-text-faint'}>
                    {selectedDoc ? selectedDoc.filename : 'Select a document to chat...'}
                  </span>
                  <ChevronDown
                    size={14}
                    className={`text-text-faint transition-transform duration-200 ${showDocPicker ? 'rotate-180' : ''}`}
                  />
                </button>

                {showDocPicker && (
                  <div
                    className="absolute top-full left-0 right-0 mt-1 rounded-xl py-1 z-20 max-h-48 overflow-y-auto"
                    style={{
                      background: 'rgba(15, 23, 42, 0.95)',
                      backdropFilter: 'blur(16px)',
                      border: '1px solid rgba(148, 163, 184, 0.12)',
                      boxShadow: '0 16px 48px rgba(0,0,0,0.4)',
                    }}
                  >
                    {readyDocs.length === 0 ? (
                      <p className="px-4 py-3 text-xs text-text-faint">No documents ready yet. Upload and process a document first.</p>
                    ) : (
                      readyDocs.map((doc: Document) => (
                        <button
                          key={doc.id}
                          onClick={() => {
                            setSelectedDocId(doc.id);
                            setShowDocPicker(false);
                          }}
                          className={`w-full text-left px-4 py-2.5 text-sm hover:bg-primary/10 transition-colors flex items-center gap-3 ${
                            selectedDocId === doc.id ? 'text-primary-light bg-primary/5' : 'text-text-muted'
                          }`}
                        >
                          <FileText size={14} className="shrink-0" />
                          <span className="truncate">{doc.filename}</span>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Chat Body */}
            <div className="flex-1 min-h-0">
              {selectedDoc ? (
                <ChatWindow documentId={selectedDoc.id} />
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center px-6">
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                    style={{ background: 'rgba(99,102,241,0.1)' }}
                  >
                    <MessageSquare size={28} className="text-primary-light opacity-50" />
                  </div>
                  <p className="text-sm font-medium text-text-muted">Select a document</p>
                  <p className="text-xs text-text-faint mt-1">Choose a processed document above to start chatting</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
