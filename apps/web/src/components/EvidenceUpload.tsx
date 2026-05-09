import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Camera, Image as ImageIcon, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api, fetchEvidenceBlob } from '../api/client';
import type { ChecklistEvidence } from '../types';

export function EvidenceUpload({ itemId }: { itemId: number }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ['checklist-evidences', itemId],
    queryFn: () => api.checklistItemEvidences(itemId)
  });

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadChecklistEvidence(itemId, file),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['checklist-evidences', itemId] });
    },
    onError: (uploadError) => setError(uploadError.message)
  });

  return (
    <div className="mt-3 rounded-lg border border-lia-red/10 bg-lia-cream/60 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.12em] text-lia-burgundy">
          <Camera size={15} className="text-lia-red" />
          Evidencias
        </div>
        <label className="focus-ring inline-flex cursor-pointer items-center gap-2 rounded-lg bg-white px-3 py-2 text-xs font-bold text-lia-burgundy shadow-sm">
          {upload.isPending ? <Loader2 size={14} className="animate-spin" /> : <ImageIcon size={14} />}
          Enviar foto
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="sr-only"
            disabled={upload.isPending}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                upload.mutate(file);
              }
              event.currentTarget.value = '';
            }}
          />
        </label>
      </div>

      {error ? <p className="mt-2 text-xs font-semibold text-lia-red">{error}</p> : null}
      {query.isLoading ? <p className="mt-2 text-xs text-lia-muted">Carregando evidencias...</p> : null}
      {query.data?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {query.data.map((evidence) => (
            <EvidenceThumbnail key={evidence.id} evidence={evidence} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function EvidenceThumbnail({ evidence }: { evidence: ChecklistEvidence }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    if (!evidence.file_url) {
      return undefined;
    }

    fetchEvidenceBlob(evidence.file_url)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        if (active) {
          setSrc(objectUrl);
        }
      })
      .catch(() => {
        if (active) {
          setSrc(null);
        }
      });

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [evidence.file_url]);

  return (
    <a
      href={src ?? undefined}
      target="_blank"
      rel="noreferrer"
      className="focus-ring block overflow-hidden rounded-lg border border-lia-red/10 bg-white"
      title={evidence.original_filename}
    >
      {src ? (
        <img src={src} alt={evidence.original_filename} className="h-16 w-16 object-cover" />
      ) : (
        <div className="flex h-16 w-16 items-center justify-center text-lia-muted">
          <ImageIcon size={18} />
        </div>
      )}
    </a>
  );
}
