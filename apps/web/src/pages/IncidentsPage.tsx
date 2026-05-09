import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Plus } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { api } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import type { IncidentCategory, IncidentSeverity, IncidentStatus, OperationalIncidentCreate } from '../types';

const categories: IncidentCategory[] = [
  'estoque',
  'limpeza',
  'equipamento',
  'atendimento',
  'delivery',
  'caixa',
  'validade',
  'outro'
];
const severities: IncidentSeverity[] = ['baixa', 'media', 'alta', 'critica'];
const statuses: Array<IncidentStatus | 'todas'> = ['todas', 'aberta', 'em_andamento', 'resolvida', 'cancelada'];

const initialForm: OperationalIncidentCreate = {
  store: 'Grupo Lia',
  category: 'outro',
  severity: 'media',
  description: ''
};

export function IncidentsPage() {
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | 'todas'>('todas');
  const [form, setForm] = useState<OperationalIncidentCreate>(initialForm);
  const queryClient = useQueryClient();

  const incidents = useQuery({
    queryKey: ['incidents', statusFilter],
    queryFn: () => api.incidents({ status: statusFilter })
  });

  const createIncident = useMutation({
    mutationFn: api.createIncident,
    onSuccess: () => {
      setForm(initialForm);
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-incidents'] });
    }
  });

  const resolveIncident = useMutation({
    mutationFn: (incidentId: number) => api.updateIncident(incidentId, { status: 'resolvida' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['incidents'] })
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createIncident.mutate(form);
  }

  return (
    <>
      <PageHeader
        eyebrow="Operacao"
        title="Ocorrencias operacionais"
        description="Registre problemas do turno e acompanhe o que esta aberto, em andamento ou resolvido."
      />

      <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <form onSubmit={submit} className="surface rounded-lg p-4">
          <div className="mb-4 flex items-center gap-2">
            <Plus className="text-lia-red" size={20} />
            <h3 className="text-lg font-black text-lia-burgundy">Nova ocorrencia</h3>
          </div>
          <div className="grid gap-3">
            <label className="text-sm font-bold text-lia-burgundy">
              Loja
              <select
                className="focus-ring mt-2 w-full rounded-lg border border-lia-red/15 bg-white px-3 py-3"
                value={form.store}
                onChange={(event) => setForm((current) => ({ ...current, store: event.target.value }))}
              >
                <option>Grupo Lia</option>
                <option>Lia Burguer</option>
                <option>Lia Pizza</option>
                <option>Lia Salgados</option>
              </select>
            </label>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm font-bold text-lia-burgundy">
                Categoria
                <select
                  className="focus-ring mt-2 w-full rounded-lg border border-lia-red/15 bg-white px-3 py-3"
                  value={form.category}
                  onChange={(event) => setForm((current) => ({ ...current, category: event.target.value as IncidentCategory }))}
                >
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>

              <label className="text-sm font-bold text-lia-burgundy">
                Severidade
                <select
                  className="focus-ring mt-2 w-full rounded-lg border border-lia-red/15 bg-white px-3 py-3"
                  value={form.severity}
                  onChange={(event) => setForm((current) => ({ ...current, severity: event.target.value as IncidentSeverity }))}
                >
                  {severities.map((severity) => (
                    <option key={severity} value={severity}>
                      {severity}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="text-sm font-bold text-lia-burgundy">
              Descricao
              <textarea
                className="focus-ring mt-2 min-h-32 w-full rounded-lg border border-lia-red/15 bg-white p-3"
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                placeholder="Ex.: equipamento apresentou falha durante o turno..."
                required
              />
            </label>

            {createIncident.error ? <p className="text-sm font-semibold text-lia-red">{createIncident.error.message}</p> : null}
            <button
              type="submit"
              disabled={createIncident.isPending}
              className="focus-ring rounded-lg bg-lia-red px-4 py-3 font-bold text-white disabled:opacity-60"
            >
              {createIncident.isPending ? 'Registrando...' : 'Registrar ocorrencia'}
            </button>
          </div>
        </form>

        <div className="surface rounded-lg p-4">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-black text-lia-burgundy">Acompanhamento</h3>
              <p className="text-sm text-lia-muted">Filtre por status e resolva ocorrencias simples.</p>
            </div>
            <select
              className="focus-ring rounded-lg border border-lia-red/15 bg-white px-3 py-2 text-sm font-semibold"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as IncidentStatus | 'todas')}
            >
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          {incidents.isLoading ? <p className="text-sm text-lia-muted">Carregando ocorrencias...</p> : null}
          {incidents.error ? <p className="rounded-lg bg-lia-red/10 p-3 text-sm text-lia-red">{incidents.error.message}</p> : null}
          <div className="space-y-3">
            {incidents.data?.map((incident) => (
              <article
                key={incident.id}
                className={`rounded-lg border bg-white p-3 ${
                  incident.severity === 'alta' || incident.severity === 'critica'
                    ? 'border-lia-red/35'
                    : 'border-lia-red/10'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <SeverityBadge severity={incident.severity} />
                      <StatusBadge status={incident.status} />
                    </div>
                    <h4 className="mt-2 font-black text-lia-burgundy">{incident.store}</h4>
                    <p className="text-xs uppercase tracking-[0.14em] text-lia-muted">{incident.category}</p>
                  </div>
                  {incident.status !== 'resolvida' ? (
                    <button
                      onClick={() => resolveIncident.mutate(incident.id)}
                      disabled={resolveIncident.isPending}
                      className="focus-ring inline-flex items-center gap-2 rounded-lg bg-lia-green px-3 py-2 text-xs font-bold text-white"
                    >
                      <CheckCircle2 size={15} /> Resolver
                    </button>
                  ) : null}
                </div>
                <p className="mt-3 text-sm leading-6 text-lia-ink">{incident.description}</p>
                <div className="mt-3 flex items-center gap-2 text-xs text-lia-muted">
                  <AlertTriangle size={14} />
                  {new Date(incident.created_at).toLocaleString()} por {incident.created_by ?? 'usuario'}
                </div>
              </article>
            ))}
            {!incidents.isLoading && !incidents.data?.length ? (
              <p className="rounded-lg bg-white p-3 text-sm text-lia-muted">Nenhuma ocorrencia encontrada.</p>
            ) : null}
          </div>
        </div>
      </section>
    </>
  );
}

function SeverityBadge({ severity }: { severity: IncidentSeverity }) {
  const classes = {
    baixa: 'bg-lia-green/10 text-lia-green',
    media: 'bg-lia-amber/10 text-lia-amber',
    alta: 'bg-lia-red/10 text-lia-red',
    critica: 'bg-lia-burgundy text-white'
  };
  return <span className={`rounded-lg px-2 py-1 text-xs font-bold ${classes[severity]}`}>{severity}</span>;
}

function StatusBadge({ status }: { status: IncidentStatus }) {
  const classes = {
    aberta: 'bg-lia-red/10 text-lia-red',
    em_andamento: 'bg-lia-amber/10 text-lia-amber',
    resolvida: 'bg-lia-green/10 text-lia-green',
    cancelada: 'bg-lia-muted/10 text-lia-muted'
  };
  return <span className={`rounded-lg px-2 py-1 text-xs font-bold ${classes[status]}`}>{status}</span>;
}
