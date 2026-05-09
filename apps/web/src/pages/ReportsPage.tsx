import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, BarChart3, CheckCircle2, ClipboardList } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useState } from 'react';
import { api } from '../api/client';
import { PageHeader } from '../components/PageHeader';

function toDateInput(date: Date) {
  return date.toISOString().slice(0, 10);
}

function daysAgo(days: number) {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return toDateInput(date);
}

const today = toDateInput(new Date());

export function ReportsPage() {
  const [startDate, setStartDate] = useState(daysAgo(6));
  const [endDate, setEndDate] = useState(today);
  const [store, setStore] = useState('');

  const summary = useQuery({
    queryKey: ['reports-summary', startDate, endDate, store],
    queryFn: () => api.reportSummary({ startDate, endDate, store: store || undefined })
  });

  const data = summary.data;

  return (
    <>
      <PageHeader
        eyebrow="Gestao"
        title="Relatorios operacionais"
        description="Resumo semanal ou mensal para acompanhar checklists, pendencias, ocorrencias e evidencias enviadas."
      />

      <section className="surface mb-5 grid gap-3 rounded-lg p-4 lg:grid-cols-[auto_auto_1fr_auto] lg:items-end">
        <div className="flex gap-2">
          <button
            className="focus-ring rounded-lg bg-lia-red px-3 py-2 text-sm font-bold text-white"
            onClick={() => {
              setStartDate(daysAgo(6));
              setEndDate(today);
            }}
          >
            7 dias
          </button>
          <button
            className="focus-ring rounded-lg bg-lia-burgundy px-3 py-2 text-sm font-bold text-white"
            onClick={() => {
              setStartDate(daysAgo(29));
              setEndDate(today);
            }}
          >
            30 dias
          </button>
        </div>
        <label className="text-sm font-bold text-lia-burgundy">
          Inicio
          <input
            className="focus-ring mt-2 w-full rounded-lg border border-lia-red/15 bg-white px-3 py-2"
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
        </label>
        <label className="text-sm font-bold text-lia-burgundy">
          Fim
          <input
            className="focus-ring mt-2 w-full rounded-lg border border-lia-red/15 bg-white px-3 py-2"
            type="date"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
          />
        </label>
        <label className="text-sm font-bold text-lia-burgundy">
          Loja
          <select
            className="focus-ring mt-2 w-full rounded-lg border border-lia-red/15 bg-white px-3 py-2"
            value={store}
            onChange={(event) => setStore(event.target.value)}
          >
            <option value="">Todas</option>
            <option>Grupo Lia</option>
            <option>Lia Burguer</option>
            <option>Lia Pizza</option>
            <option>Lia Salgados</option>
          </select>
        </label>
      </section>

      {summary.isLoading ? <p className="text-sm text-lia-muted">Carregando relatorio...</p> : null}
      {summary.error ? <p className="rounded-lg bg-lia-red/10 p-3 text-sm text-lia-red">{summary.error.message}</p> : null}

      {data ? (
        <>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <ReportCard label="Conclusao geral" value={`${data.completion_percent}%`} icon={CheckCircle2} tone="green" />
            <ReportCard label="Tarefas pendentes" value={data.pending_tasks} icon={ClipboardList} tone="amber" />
            <ReportCard label="Ocorrencias abertas" value={data.incidents_by_status.aberta ?? 0} icon={AlertTriangle} tone="red" />
            <ReportCard
              label="Ocorrencias criticas"
              value={data.incidents_by_severity.critica ?? 0}
              icon={AlertTriangle}
              tone="burgundy"
            />
          </section>

          <section className="mt-5 grid gap-4 lg:grid-cols-3">
            <Breakdown title="Por status" data={data.incidents_by_status} />
            <Breakdown title="Por severidade" data={data.incidents_by_severity} />
            <Breakdown title="Por categoria" data={data.incidents_by_category} />
          </section>

          <section className="mt-5 surface rounded-lg p-4">
            <div className="flex items-center gap-3">
              <BarChart3 className="text-lia-red" />
              <div>
                <h3 className="text-lg font-black text-lia-burgundy">Resumo do periodo</h3>
                <p className="text-sm text-lia-muted">
                  {data.total_checklists} checklists, {data.completed_items} de {data.total_items} itens concluidos,
                  {` ${data.total_incidents} ocorrencias e ${data.evidences_uploaded} evidencias enviadas.`}
                </p>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </>
  );
}

function ReportCard({
  label,
  value,
  icon: Icon,
  tone
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone: 'green' | 'amber' | 'red' | 'burgundy';
}) {
  const toneMap = {
    green: 'bg-lia-green/10 text-lia-green',
    amber: 'bg-lia-amber/10 text-lia-amber',
    red: 'bg-lia-red/10 text-lia-red',
    burgundy: 'bg-lia-burgundy text-white'
  };
  return (
    <article className="surface rounded-lg p-4">
      <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-lg ${toneMap[tone]}`}>
        <Icon size={20} />
      </div>
      <p className="text-sm font-semibold text-lia-muted">{label}</p>
      <strong className="mt-1 block text-3xl font-black text-lia-burgundy">{value}</strong>
    </article>
  );
}

function Breakdown({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  return (
    <article className="surface rounded-lg p-4">
      <h3 className="text-lg font-black text-lia-burgundy">{title}</h3>
      <div className="mt-3 space-y-2">
        {entries.length ? (
          entries.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between rounded-lg bg-white px-3 py-2 text-sm">
              <span className="font-semibold text-lia-burgundy">{label}</span>
              <strong className="text-lia-red">{value}</strong>
            </div>
          ))
        ) : (
          <p className="rounded-lg bg-white px-3 py-2 text-sm text-lia-muted">Sem registros no periodo.</p>
        )}
      </div>
    </article>
  );
}
