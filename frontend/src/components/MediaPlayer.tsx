import { useRef, useState, useImperativeHandle, forwardRef, useEffect } from 'react';
import { Clock } from 'lucide-react';
import type { FileType } from '../types';

export interface MediaPlayerHandle {
  seekTo: (seconds: number) => void;
}

interface Props {
  src: string;
  fileType: FileType;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

const MediaPlayer = forwardRef<MediaPlayerHandle, Props>(({ src, fileType }, ref) => {
  const mediaRef = useRef<HTMLVideoElement & HTMLAudioElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useImperativeHandle(ref, () => ({
    seekTo: (seconds: number) => {
      if (mediaRef.current) {
        mediaRef.current.currentTime = seconds;
        mediaRef.current.play().catch(() => {});
      }
    },
  }));

  useEffect(() => {
    const el = mediaRef.current;
    if (!el) return;

    const onTime = () => setCurrentTime(el.currentTime);
    const onMeta = () => setDuration(el.duration);

    el.addEventListener('timeupdate', onTime);
    el.addEventListener('loadedmetadata', onMeta);

    return () => {
      el.removeEventListener('timeupdate', onTime);
      el.removeEventListener('loadedmetadata', onMeta);
    };
  }, []);

  const isVideo = fileType === 'VIDEO';

  return (
    <div className="glass-card overflow-hidden">
      {isVideo ? (
        <video
          ref={mediaRef}
          src={src}
          controls
          className="w-full bg-black aspect-video"
        />
      ) : (
        <div className="p-6 pb-2">
          <audio ref={mediaRef} src={src} controls className="w-full" />
        </div>
      )}

      {/* Timestamp display */}
      <div className="px-4 py-2.5 border-t border-glass-border flex items-center justify-between text-xs text-text-faint">
        <span className="flex items-center gap-1.5">
          <Clock size={13} className="text-primary-light" />
          {formatTime(currentTime)}
        </span>
        <span>{duration > 0 ? formatTime(duration) : '--:--'}</span>
      </div>
    </div>
  );
});

MediaPlayer.displayName = 'MediaPlayer';
export default MediaPlayer;
