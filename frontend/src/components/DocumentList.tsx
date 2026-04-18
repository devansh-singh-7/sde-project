import { Link } from 'react-router-dom';
import { FileText, Film, Music, Trash2, Loader2, ArrowRight } from 'lucide-react';
import { useDocuments, useDeleteDocument } from '../hooks/useDocuments';
import type { Document } from '../types';

const typeConfig = (ft: string) => {
  if (ft === 'PDF') return { icon: FileText, color: 'text-red-400', bg: 'bg-red-500/10' };
  if (ft === 'VIDEO') return { icon: Film, color: 'text-purple-400', bg: 'bg-purple-500/10' };
  return { icon: Music, color: 'text-emerald-400', bg: 'bg-emerald-500/10' };
};

const statusBadge = (s: string) => {
  const base = 'px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase';
  if (s === 'READY') return <span className={`${base} bg-success/10 text-success`}>Ready</span>;
  if (s === 'ERROR') return <span className={`${base} bg-danger/10 text-danger`}>Error</span>;
  return (
    <span className={`${base} bg-warning/10 text-warning flex items-center gap-1`}>
      <Loader2 size={11} className="animate-spin" /> Processing
    </span>
  );
};

export default function DocumentList() {
  const { data: docs, isLoading } = useDocuments();
  const { mutate: remove } = useDeleteDocument();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 size={28} className="animate-spin text-primary-light" />
      </div>
    );
  }

  if (!docs?.length) {
    return (
      <div className="glass-card text-center py-14 px-6">
        <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
          style={{ background: 'rgba(99,102,241,0.1)' }}
        >
          <FileText size={24} className="text-text-faint" />
        </div>
        <p className="text-sm font-medium text-text-muted">No documents uploaded yet</p>
        <p className="text-xs text-text-faint mt-1">Upload a PDF, audio, or video file to get started</p>
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {docs.map((doc: Document, i: number) => {
        const config = typeConfig(doc.file_type);
        const Icon = config.icon;

        return (
          <Link
            key={doc.id || (doc as any)._id || i}
            to={`/documents/${doc.id || (doc as any)._id}`}
            className="glass-card-light flex items-center justify-between p-4 hover:border-primary/20 transition-all duration-300 group animate-fade-slide-up"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className="flex items-center gap-4 min-w-0">
              <div className={`w-10 h-10 rounded-xl ${config.bg} flex items-center justify-center shrink-0`}>
                <Icon size={20} className={config.color} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold truncate text-text group-hover:text-primary-light transition-colors">
                  {doc.filename}
                </p>
                <p className="text-xs text-text-faint mt-0.5">
                  {new Date(doc.created_at).toLocaleDateString()} · {doc.file_type}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 ml-4 shrink-0">
              {statusBadge(doc.status)}
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  remove(doc.id);
                }}
                className="p-2 text-text-faint opacity-0 group-hover:opacity-100 hover:text-danger rounded-lg transition-all duration-200"
                title="Delete"
              >
                <Trash2 size={15} />
              </button>
              <ArrowRight size={14} className="text-text-faint opacity-0 group-hover:opacity-100 transition-all duration-200" />
            </div>
          </Link>
        );
      })}
    </div>
  );
}
