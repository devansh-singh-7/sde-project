import { useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, FileText, Film, Music } from 'lucide-react';
import { useDocument } from '../hooks/useDocuments';
import ChatWindow from '../components/ChatWindow';
import MediaPlayer, { type MediaPlayerHandle } from '../components/MediaPlayer';
import Summary from '../components/Summary';

export default function DocumentPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = useDocument(id || '');
  const mediaRef = useRef<MediaPlayerHandle>(null);

  const handleTimestampClick = useCallback((seconds: number) => {
    mediaRef.current?.seekTo(seconds);
  }, []);

  if (isLoading || !data) {

    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 size={28} className="animate-spin text-primary-light" />
      </div>
    );
  }

  const { document: doc, transcript_segments: segments } = data;
  const isMedia = doc.file_type === 'AUDIO' || doc.file_type === 'VIDEO';

  const typeIcon =
    doc.file_type === 'PDF' ? (
      <FileText size={20} className="text-red-400" />
    ) : doc.file_type === 'VIDEO' ? (
      <Film size={20} className="text-purple-400" />
    ) : (
      <Music size={20} className="text-emerald-400" />
    );

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3">
        <Link
          to="/"
          className="p-2 rounded-xl text-text-faint hover:text-text hover:bg-glass-light transition-all duration-200"
        >
          <ArrowLeft size={18} />
        </Link>
        <div className="flex items-center gap-2.5">
          {typeIcon}
          <div>
            <h1 className="text-lg font-bold text-text">{doc.filename}</h1>
            <p className="text-xs text-text-faint">
              {doc.file_type} · {doc.status} · {new Date(doc.created_at).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {doc.status === 'PROCESSING' && (
        <div className="glass-card px-5 py-3 flex items-center gap-3 text-sm text-warning"
          style={{ borderLeft: '3px solid rgba(251, 191, 36, 0.5)' }}
        >
          <Loader2 size={16} className="animate-spin" />
          Document is being processed. Chat will be available once ready.
        </div>
      )}

      {doc.status === 'ERROR' && (
        <div className="glass-card px-5 py-3 text-sm text-danger"
          style={{ borderLeft: '3px solid rgba(248, 113, 113, 0.5)' }}
        >
          Processing failed. Please try re-uploading the file.
        </div>
      )}

      {/* Main layout: two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Left: Media / Summary / Transcript */}
        <div className="lg:col-span-2 space-y-4">
          {isMedia ? (
            <MediaPlayer
              ref={mediaRef}
              src={`/${doc.file_path}`}
              fileType={doc.file_type}
            />
          ) : (
            <div className="glass-card w-full h-[600px] overflow-hidden rounded-xl border border-glass-border">
              <iframe src={`/${doc.file_path}`} className="w-full h-full" title="PDF Viewer" />
            </div>
          )}

          <Summary documentId={doc.id} existingSummary={doc.summary} />

          {/* Transcript segments */}
          {segments.length > 0 && (
            <div className="glass-card p-5 max-h-80 overflow-y-auto">
              <h3 className="text-sm font-semibold mb-3 text-text-muted">Transcript</h3>
              <div className="space-y-1">
                {segments.map((seg) => (
                  <button
                    key={seg.id}
                    onClick={() => handleTimestampClick(seg.start_time)}
                    className="flex gap-3 text-sm w-full text-left hover:bg-glass-light rounded-lg px-2 py-1.5 transition-all group"
                  >
                    <span className="text-xs text-primary-light font-mono shrink-0 pt-0.5 w-14 text-right group-hover:font-bold transition-all">
                      {Math.floor(seg.start_time / 60)}:
                      {Math.floor(seg.start_time % 60)
                        .toString()
                        .padStart(2, '0')}
                    </span>
                    <p className="text-text-muted leading-relaxed">{seg.text}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Chat */}
        <div className="lg:col-span-3 h-[calc(100vh-12rem)]">
          {doc.status === 'READY' ? (
            <div className="glass-card h-full overflow-hidden">
              <ChatWindow
                documentId={doc.id}
                onTimestampClick={handleTimestampClick}
              />
            </div>
          ) : (
            <div className="glass-card h-full flex items-center justify-center text-text-faint text-sm">
              Chat available after processing completes
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
