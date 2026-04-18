import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { getDocuments, getDocument, deleteDocument, uploadDocument } from '../api/documents';

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: () => getDocuments(),
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => getDocument(id),
    enabled: !!id && id !== 'undefined',
    refetchInterval: (query) => {
      if (query.state.data?.document?.status === 'PROCESSING') return 3000;
      return false;
    },
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadDocument(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] });
      toast.success('File uploaded successfully!');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || 'Upload failed';
      toast.error(msg);
    },
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document deleted');
    },
    onError: () => {
      toast.error('Delete failed');
    },
  });
}
