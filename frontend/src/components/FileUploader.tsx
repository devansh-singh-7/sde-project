import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileText, Film, Music, Upload, CheckCircle, AlertCircle, Loader2, X, CloudUpload } from 'lucide-react';
import { uploadDocument } from '../api/documents';
import toast from 'react-hot-toast';

const ACCEPT_MAP: Record<string, string[]> = {
  'application/pdf': ['.pdf'],
  'audio/mpeg': ['.mp3'],
  'audio/wav': ['.wav'],
  'video/mp4': ['.mp4'],
  'video/quicktime': ['.mov'],
  'video/x-msvideo': ['.avi'],
};

const MAX_SIZE = 500 * 1024 * 1024; // 500 MB

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'ready' | 'error';

function getFileCategory(file: File): 'pdf' | 'audio' | 'video' {
  if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) return 'pdf';
  if (file.type.startsWith('audio/')) return 'audio';
  return 'video';
}

function FileIcon({ category, size = 24 }: { category: 'pdf' | 'audio' | 'video'; size?: number }) {
  if (category === 'pdf') return <FileText size={size} className="text-red-400" />;
  if (category === 'audio') return <Music size={size} className="text-emerald-400" />;
  return <Film size={size} className="text-cyan-400" />;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

interface Props {
  onUploadComplete?: (documentId: string) => void;
}

export default function FileUploader({ onUploadComplete }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const onDrop = useCallback((accepted: File[], rejected: { errors: { message: string }[] }[]) => {
    if (rejected.length > 0) {
      const err = rejected[0].errors[0];
      if (err.message.includes('too large') || err.message.includes('larger')) {
        toast.error('File exceeds the 500 MB size limit');
      } else {
        toast.error('Unsupported file type');
      }
      return;
    }
    if (accepted[0]) {
      setSelectedFile(accepted[0]);
      setStatus('idle');
      setProgress(0);
      setErrorMsg('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (accepted, fileRejections) => {
        onDrop(accepted, fileRejections as any);
    },
    accept: ACCEPT_MAP,
    maxSize: MAX_SIZE,
    multiple: false,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    setStatus('uploading');
    setProgress(0);
    setErrorMsg('');

    try {
      const res = await uploadDocument(selectedFile, (pct) => setProgress(pct));
      setStatus('processing');

      setTimeout(() => {
        setStatus('ready');
        onUploadComplete?.(res.document_id);
      }, 1500);
    } catch (err: any) {
      setStatus('error');
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 413) {
        setErrorMsg('File exceeds the maximum allowed size');
      } else if (err?.response?.status === 415) {
        setErrorMsg('Unsupported file type');
      } else {
        setErrorMsg(detail || 'Upload failed. Please try again.');
      }
      toast.error(detail || 'Upload failed');
    }
  };

  const reset = () => {
    setSelectedFile(null);
    setStatus('idle');
    setProgress(0);
    setErrorMsg('');
  };

  const category = selectedFile ? getFileCategory(selectedFile) : null;

  return (
    <div className="glass-card p-6">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
        <CloudUpload size={18} className="text-primary-light" />
        Upload Document
      </h3>

      {/* ─── Dropzone ─── */}
      <div
        {...getRootProps()}
        className={`
          relative rounded-xl p-8 text-center cursor-pointer transition-all duration-300
          ${isDragActive
            ? 'scale-[1.01]'
            : ''
          }
        `}
        style={{
          border: isDragActive
            ? '2px dashed rgba(99, 102, 241, 0.6)'
            : '2px dashed rgba(148, 163, 184, 0.15)',
          background: isDragActive
            ? 'rgba(99, 102, 241, 0.05)'
            : 'rgba(15, 23, 42, 0.3)',
        }}
      >
        <input {...getInputProps()} />
        <div className={`transition-transform duration-300 ${isDragActive ? 'scale-110' : ''}`}>
          <Upload size={32} className={`mx-auto mb-3 ${isDragActive ? 'text-primary-light' : 'text-text-faint'}`} />
        </div>
        <p className="text-sm text-text-muted">
          <span className="font-medium text-primary-light">Click to browse</span> or drag & drop
        </p>
        <p className="text-xs text-text-faint mt-1.5">PDF, MP3, MP4, WAV, MOV, AVI — up to 500 MB</p>
      </div>

      {/* ─── File Preview + Progress ─── */}
      {selectedFile && (
        <div className="mt-4 glass-card-light overflow-hidden">
          {/* File info row */}
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3 min-w-0">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                category === 'pdf' ? 'bg-red-500/10' : category === 'audio' ? 'bg-emerald-500/10' : 'bg-cyan-500/10'
              }`}>
                <FileIcon category={category!} size={22} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium truncate text-text">{selectedFile.name}</p>
                <p className="text-xs text-text-faint">{formatSize(selectedFile.size)}</p>
              </div>
            </div>

            <div className="flex items-center gap-2 ml-3 shrink-0">
              {/* Status indicator */}
              {status === 'ready' && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-success bg-success/10 px-2.5 py-1 rounded-full">
                  <CheckCircle size={14} /> Ready
                </span>
              )}
              {status === 'processing' && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-warning bg-warning/10 px-2.5 py-1 rounded-full">
                  <Loader2 size={14} className="animate-spin" /> Processing
                </span>
              )}
              {status === 'error' && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-danger bg-danger/10 px-2.5 py-1 rounded-full">
                  <AlertCircle size={14} /> Error
                </span>
              )}

              {/* Action buttons */}
              {status === 'idle' && (
                <button onClick={handleUpload} className="btn-primary !px-4 !py-2 !text-xs">
                  Upload
                </button>
              )}
              {(status === 'idle' || status === 'ready' || status === 'error') && (
                <button
                  onClick={reset}
                  className="p-2 text-text-faint hover:text-danger rounded-lg transition-all"
                  title="Remove"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          </div>

          {/* Progress bar */}
          {(status === 'uploading' || status === 'processing') && (
            <div className="px-4 pb-4">
              <div className="w-full h-1.5 bg-glass-border rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ease-out ${
                    status === 'processing' ? 'shimmer-bar w-full' : ''
                  }`}
                  style={status === 'uploading' ? {
                    width: `${progress}%`,
                    background: 'linear-gradient(90deg, #6366F1, #22D3EE)',
                  } : undefined}
                />
              </div>
              <p className="text-xs text-text-faint mt-1.5">
                {status === 'uploading' ? `Uploading… ${progress}%` : 'Processing document…'}
              </p>
            </div>
          )}

          {/* Error message */}
          {status === 'error' && errorMsg && (
            <div className="px-4 pb-4">
              <p className="text-xs text-danger bg-danger/5 border border-danger/20 rounded-lg px-3 py-2">
                {errorMsg}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
