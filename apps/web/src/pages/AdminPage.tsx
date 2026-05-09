import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, BookOpen, Camera, ClipboardList, FileText, Store, Users } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { api } from '../api/client';
import { EvidenceThumbnail } from '../components/EvidenceUpload';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../contexts/useAuth';
import type { Role, StoreOption, User, UserCreate } from '../types';

const emptyUser: UserCreate = {
  username: '',
  name: '',
  role: 'operacao',
  password: ''
};

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
        description="Gerencie usuarios, lojas e acompanhe os principais dados internos da Central LIA."
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
        <AdminCard title="Relatorios" value="Resumo ativo" icon={FileText} loading={false} />
      </section>

      <section className="mt-5 grid gap-4 xl:grid-cols-2">
        <UsersAdminSection currentUserId={user?.id ?? 0} users={users.data ?? []} loading={users.isLoading} />
        <StoresAdminSection stores={stores.data ?? []} loading={stores.isLoading} />
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="surface rounded-lg p-4">
          <h3 className="text-lg font-black text-lia-burgundy">Templates e manuais</h3>
          <div className="mt-3 grid gap-2">
            <div className="rounded-lg bg-white px-3 py-2 text-sm text-lia-muted">
              {templates.data?.length ?? 0} templates de checklist cadastrados.
            </div>
            <div className="rounded-lg bg-white px-3 py-2 text-sm text-lia-muted">
              {manuals.data?.length ?? 0} manuais tecnicos cadastrados.
            </div>
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
            Exclusoes de usuario e loja sao tratadas como desativacao para preservar historico de operacao,
            ocorrencias, checklists e evidencias.
          </p>
        </div>
      </section>
    </>
  );
}

function UsersAdminSection({
  currentUserId,
  users,
  loading
}: {
  currentUserId: number;
  users: User[];
  loading: boolean;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<UserCreate>(emptyUser);

  const createUser = useMutation({
    mutationFn: api.createAdminUser,
    onSuccess: () => {
      setForm(emptyUser);
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    }
  });

  const updateUser = useMutation({
    mutationFn: ({ userId, payload }: { userId: number; payload: Partial<Pick<User, 'name' | 'role' | 'active'>> }) =>
      api.updateAdminUser(userId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createUser.mutate(form);
  }

  return (
    <div className="surface rounded-lg p-4">
      <h3 className="text-lg font-black text-lia-burgundy">Usuarios</h3>
      <form onSubmit={submit} className="mt-3 grid gap-3 rounded-lg bg-white p-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="usuario"
            value={form.username}
            onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
            required
          />
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="nome"
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            required
          />
          <select
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            value={form.role}
            onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as Role }))}
          >
            <option value="operacao">operacao</option>
            <option value="admin">admin</option>
          </select>
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="senha inicial"
            type="password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            required
          />
        </div>
        {createUser.error ? <p className="text-sm font-semibold text-lia-red">{createUser.error.message}</p> : null}
        <button
          className="focus-ring rounded-lg bg-lia-red px-3 py-2 text-sm font-bold text-white disabled:opacity-60"
          disabled={createUser.isPending}
        >
          {createUser.isPending ? 'Criando...' : 'Criar usuario'}
        </button>
      </form>

      <div className="mt-3 space-y-2">
        {loading ? <p className="text-sm text-lia-muted">Carregando usuarios...</p> : null}
        {users.map((item) => (
          <div key={item.id} className="rounded-lg bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-bold text-lia-burgundy">{item.name}</p>
                <p className="text-xs text-lia-muted">@{item.username}</p>
              </div>
              <StatusPill active={item.active} />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
                onClick={() =>
                  updateUser.mutate({ userId: item.id, payload: { role: item.role === 'admin' ? 'operacao' : 'admin' } })
                }
              >
                Tornar {item.role === 'admin' ? 'operacao' : 'admin'}
              </button>
              <button
                className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy disabled:opacity-50"
                disabled={item.id === currentUserId}
                onClick={() => updateUser.mutate({ userId: item.id, payload: { active: !item.active } })}
              >
                {item.active ? 'Desativar' : 'Ativar'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StoresAdminSection({ stores, loading }: { stores: StoreOption[]; loading: boolean }) {
  const queryClient = useQueryClient();
  const [storeName, setStoreName] = useState('');

  const createStore = useMutation({
    mutationFn: api.createAdminStore,
    onSuccess: () => {
      setStoreName('');
      queryClient.invalidateQueries({ queryKey: ['admin-stores'] });
    }
  });

  const updateStore = useMutation({
    mutationFn: ({ storeId, payload }: { storeId: number; payload: Partial<Pick<StoreOption, 'name' | 'active'>> }) =>
      api.updateAdminStore(storeId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-stores'] })
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createStore.mutate(storeName);
  }

  return (
    <div className="surface rounded-lg p-4">
      <h3 className="text-lg font-black text-lia-burgundy">Lojas</h3>
      <form onSubmit={submit} className="mt-3 flex gap-2 rounded-lg bg-white p-3">
        <input
          className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          placeholder="Nome da loja"
          value={storeName}
          onChange={(event) => setStoreName(event.target.value)}
          required
        />
        <button
          className="focus-ring rounded-lg bg-lia-red px-3 py-2 text-sm font-bold text-white disabled:opacity-60"
          disabled={createStore.isPending}
        >
          Criar
        </button>
      </form>
      {createStore.error ? <p className="mt-2 text-sm font-semibold text-lia-red">{createStore.error.message}</p> : null}

      <div className="mt-3 space-y-2">
        {loading ? <p className="text-sm text-lia-muted">Carregando lojas...</p> : null}
        {stores.map((store) => (
          <StoreRow key={store.id} store={store} onSave={(payload) => updateStore.mutate({ storeId: store.id, payload })} />
        ))}
      </div>
    </div>
  );
}

function StoreRow({
  store,
  onSave
}: {
  store: StoreOption;
  onSave: (payload: Partial<Pick<StoreOption, 'name' | 'active'>>) => void;
}) {
  const [name, setName] = useState(store.name);

  return (
    <div className="rounded-lg bg-white p-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 px-3 py-2 text-sm font-semibold text-lia-burgundy"
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <StatusPill active={store.active} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ name })}
        >
          Salvar nome
        </button>
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ active: !store.active })}
        >
          {store.active ? 'Desativar' : 'Ativar'}
        </button>
      </div>
    </div>
  );
}

function StatusPill({ active }: { active: boolean }) {
  return (
    <span
      className={`rounded-lg px-2 py-1 text-xs font-bold ${
        active ? 'bg-lia-green/10 text-lia-green' : 'bg-lia-muted/10 text-lia-muted'
      }`}
    >
      {active ? 'Ativo' : 'Inativo'}
    </span>
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
