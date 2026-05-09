import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, BookOpen, Camera, ClipboardList, FileText, Store, Users } from 'lucide-react';
import { api } from '../api/client';
import { EvidenceThumbnail } from '../components/EvidenceUpload';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../contexts/useAuth';

export function AdminPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const users = useQuery({ queryKey: ['admin-users'], queryFn: api.adminUsers, enabled: isAdmin });
  const stores = useQuery({ queryKey: ['admin-stores'], queryFn: api.adminStores, enabled: isAdmin });
  const templates = useQuery({
    queryKey: ['admin-checklist-templates'],
    queryFn: api.adminChecklistTemplates,
    enabled: isAdmin
  });
  const manuals = useQuery({ queryKey: ['admin-manuals'], queryFn: api.adminManuals, enabled: isAdmin });
  const incidents = useQuery({ queryKey: ['admin-incidents'], queryFn: () => api.incidents(), enabled: isAdmin });
  const evidences = useQuery({ queryKey: ['admin-evidences'], queryFn: () => api.evidenceAudit(), enabled: isAdmin });

  if (!isAdmin) {
    return (
      <>
        <PageHeader
          eyebrow="Admin"
          title="Acesso restrito"
          description="Esta area sera usada pela gestao para acompanhar dados internos da Central LIA."
        />
        <div className="surface rounded-lg p-4 text-sm font-semibold text-lia-burgundy">
          Seu usuario ainda nao possui perfil administrativo.
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Gestao"
        title="Painel administrativo"
        description="Base inicial para acompanhar usuarios, lojas, checklists, manuais, ocorrencias, evidencias e relatorios."
      />

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <AdminCard title="Usuarios" value={users.data?.length ?? 0} icon={Users} loading={users.isLoading} />
        <AdminCard title="Lojas" value={stores.data?.length ?? 0} icon={Store} loading={stores.isLoading} />
        <AdminCard
          title="Templates de checklist"
          value={templates.data?.length ?? 0}
          icon={ClipboardList}
          loading={templates.isLoading}
        />
        <AdminCard title="Manuais" value={manuals.data?.length ?? 0} icon={BookOpen} loading={manuals.isLoading} />
        <AdminCard
          title="Ocorrencias"
          value={incidents.data?.length ?? 0}
          icon={AlertTriangle}
          loading={incidents.isLoading}
        />
        <AdminCard
          title="Relatorios"
          value="Resumo ativo"
          icon={FileText}
          loading={false}
        />
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="surface rounded-lg p-4">
          <h3 className="text-lg font-black text-lia-burgundy">Lojas cadastradas</h3>
          <div className="mt-3 grid gap-2">
            {stores.data?.map((store) => (
              <div key={store.name} className="rounded-lg bg-white px-3 py-2 text-sm font-semibold text-lia-burgundy">
                {store.name}
              </div>
            ))}
          </div>
        </div>

        <div className="surface rounded-lg p-4">
          <h3 className="text-lg font-black text-lia-burgundy">Auditoria de evidencias</h3>
          {evidences.isLoading ? <p className="mt-3 text-sm text-lia-muted">Carregando evidencias...</p> : null}
          {evidences.data?.length ? (
            <div className="mt-3 space-y-3">
              {evidences.data.slice(0, 8).map((evidence) => (
                <div key={evidence.id} className="flex gap-3 rounded-lg bg-white p-3">
                  <EvidenceThumbnail evidence={evidence} />
                  <div className="min-w-0 text-sm">
                    <p className="font-bold text-lia-burgundy">{evidence.store ?? 'Grupo Lia'}</p>
                    <p className="truncate text-lia-muted">{evidence.item_text ?? evidence.original_filename}</p>
                    <p className="mt-1 text-xs text-lia-muted">
                      {new Date(evidence.created_at).toLocaleString()} por {evidence.uploaded_by ?? 'usuario'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-lia-muted">Nenhuma evidencia enviada ainda.</p>
          )}
        </div>
      </section>

      <section className="mt-5 rounded-lg border border-lia-red/10 bg-white/70 p-4">
        <div className="flex items-start gap-3">
          <Camera className="mt-1 text-lia-red" size={20} />
          <p className="text-sm leading-6 text-lia-muted">
            Esta tela entrega a base administrativa. Os proximos passos naturais sao CRUD de usuarios, edicao de
            manuais e configuracao dos templates pelo proprio gestor.
          </p>
        </div>
      </section>
    </>
  );
}

function AdminCard({
  title,
  value,
  icon: Icon,
  loading
}: {
  title: string;
  value: string | number;
  icon: typeof Users;
  loading: boolean;
}) {
  return (
    <article className="surface rounded-lg p-4">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-lia-red/10 text-lia-red">
        <Icon size={20} />
      </div>
      <p className="text-sm font-semibold text-lia-muted">{title}</p>
      <strong className="mt-1 block text-2xl font-black text-lia-burgundy">{loading ? '...' : value}</strong>
    </article>
  );
}
