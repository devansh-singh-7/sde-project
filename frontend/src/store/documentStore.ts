import { create } from 'zustand';

interface DocumentState {
  currentMediaTime: number;
  seekTo: number | null;
  setCurrentMediaTime: (t: number) => void;
  setSeekTo: (t: number | null) => void;
}

export const useDocumentStore = create<DocumentState>()((set) => ({
  currentMediaTime: 0,
  seekTo: null,
  setCurrentMediaTime: (t) => set({ currentMediaTime: t }),
  setSeekTo: (t) => set({ seekTo: t }),
}));
