import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, Save } from 'lucide-react';
import { useState } from 'react';
import { api } from '../api/client';
import { EvidenceUpload } from '../components/EvidenceUpload';
import { PageHeader } from '../components/PageHeader';
import { ProgressBar } from '../components/ProgressBar';

const today = new Date().toISOString().slice(0, 10);

export function ChecklistsPage() {
  const [date, setDate] = useState(today);
  const [store, setStore] = useState('Grupo Lia');
  const [notes, setNotes] = useState<Record<number, string>>({});
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['checklists', date, store],
    queryFn: () => api.checklists(date, store)
  });

  const toggle = useMutation({
    mutationFn: ({ runId, itemId, done }: { runId: number; itemId: number; done: boolean }) =>
      api.updateChecklistItem(runId, itemId, done),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['checklists', date, store] })
  });

  const saveNote = useMutation({
    mutationFn: ({ runId, note }: { runId: number; note: string }) => api.updateClosingNote(runId, note),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['checklists', date, store] })
  });

  return (
    <>
      <PageHeader
        eyebrow="Execução"
        title="Checklists persistentes"
        description="Marque tarefas por data e registre observações de fechamento. Cada mudança fica salva no backend."
      />

      <section className="surface mb-5 grid gap-3 rounded-lg p-4 md:grid-cols-[1fr_1fr_auto] md:items-end">
        <label className="text-sm font-bold text-lia-burgundy">
          Data
          <div className="mt-2 flex items-center gap-2 rounded-lg border border-lia-red/15 bg-white px-3 py-2">
            <CalendarDays size={18} className="text-lia-red" />
            <input className="w-full bg-transparent outline-none" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
        </label>
        <label className="text-sm font-bold text-lia-burgundy">
          Loja
          <select
            className="focus-ring mt-2 w-full rounded-lg border border-lia-red/15 bg-white px-3 py-3"
            value={store}
            onChange={(e) => setStore(e.target.value)}
          >
            <option>Grupo Lia</option>
            <option>Lia Burguer</option>
            <option>Lia Pizza</option>
            <option>Lia Salgados</option>
          </select>
        </label>
      </section>

      {query.isLoading ? <p className="text-lia-muted">Carregando checklists...</p> : null}
      {query.error ? <p className="rounded-lg bg-lia-red/10 p-3 text-lia-red">{query.error.message}</p> : null}

      <section className="grid gap-4 lg:grid-cols-3">
        {query.data?.map((run) => {
          const grouped = run.items.reduce<Record<string, typeof run.items>>((acc, item) => {
            acc[item.section] = acc[item.section] ?? [];
            acc[item.section].push(item);
            return acc;
          }, {});
          return (
            <article key={run.id} className="surface rounded-lg p-4">
              <div className="mb-4">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-lia-red">{run.category}</p>
                <h3 className="text-xl font-black text-lia-burgundy">{run.title}</h3>
                <div className="mt-3">
                  <ProgressBar value={run.progress} />
                  <p className="mt-2 text-sm text-lia-muted">
                    {run.completed} de {run.total} itens concluídos.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {Object.entries(grouped).map(([section, items]) => (
                  <div key={section}>
                    <h4 className="mb-2 font-bold text-lia-burgundy">{section}</h4>
                    <div className="space-y-2">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="rounded-lg border border-lia-red/10 bg-white px-3 py-3 text-sm leading-5"
                        >
                          <label className="flex gap-3">
                            <input
                              type="checkbox"
                              checked={item.done}
                              disabled={toggle.isPending}
                              onChange={(event) =>
                                toggle.mutate({ runId: run.id, itemId: item.id, done: event.target.checked })
                              }
                              className="mt-1 h-4 w-4 accent-lia-red"
                            />
                            <span className={item.done ? 'text-lia-muted line-through' : 'text-lia-ink'}>{item.text}</span>
                          </label>
                          <EvidenceUpload itemId={item.id} />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4">
                <label className="text-sm font-bold text-lia-burgundy">
                  Observação de fechamento
                  <textarea
                    value={notes[run.id] ?? run.closing_note ?? ''}
                    onChange={(event) => setNotes((current) => ({ ...current, [run.id]: event.target.value }))}
                    className="focus-ring mt-2 min-h-24 w-full rounded-lg border border-lia-red/15 bg-white p-3 text-sm"
                    placeholder="Ex.: faltou embalagem, freezer revisado, turno sem ocorrências..."
                  />
                </label>
                <button
                  onClick={() => saveNote.mutate({ runId: run.id, note: notes[run.id] ?? run.closing_note ?? '' })}
                  className="focus-ring mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-lia-burgundy px-3 py-2 text-sm font-bold text-white"
                >
                  <Save size={16} /> Salvar observação
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </>
  );
}
