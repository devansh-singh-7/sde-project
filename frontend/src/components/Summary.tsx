import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Sparkles, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { summarizeApi } from '../api/chat';

interface Props {
  documentId: string;
  existingSummary: string | null;
}

export default function Summary({ documentId, existingSummary }: Props) {
  const [summary, setSummary] = useState<string | null>(existingSummary);
  const [expanded, setExpanded] = useState(true);

  const { mutate: generate, isPending } = useMutation({
    mutationFn: () => summarizeApi(documentId),
    onSuccess: (data) => setSummary(data.summary),
  });

  return (
    <div className="glass-card overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-5 py-3.5 flex items-center justify-between border-b border-glass-border hover:bg-glass-light transition-colors"
      >
        <h3 className="font-semibold text-sm flex items-center gap-2 text-text-muted">
          <Sparkles size={16} className="text-warning" />
          AI Summary
        </h3>
        {expanded ? <ChevronUp size={16} className="text-text-faint" /> : <ChevronDown size={16} className="text-text-faint" />}
      </button>

      {expanded && (
        <div className="px-5 py-4">
          {summary ? (
            <p className="text-sm text-text-muted leading-relaxed whitespace-pre-wrap">{summary}</p>
          ) : (
            <div className="text-center py-6">
              <p className="text-sm text-text-faint mb-3">No summary generated yet.</p>
              <button
                onClick={() => generate()}
                disabled={isPending}
                className="btn-primary !px-4 !py-2 !text-xs inline-flex items-center gap-2"
              >
                {isPending ? (
                  <>
                    <Loader2 size={13} className="animate-spin" /> Generating…
                  </>
                ) : (
                  <>
                    <Sparkles size={13} /> Generate Summary
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
