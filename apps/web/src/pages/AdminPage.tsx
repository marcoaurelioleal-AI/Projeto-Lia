import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, BookOpen, Bot, Camera, ClipboardList, FileText, Store, Users } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { api } from '../api/client';
import { EvidenceThumbnail } from '../components/EvidenceUpload';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../contexts/useAuth';
import type {
  AiInteraction,
  ChecklistTemplate,
  ChecklistTemplateCreate,
  ChecklistTemplateItem,
  ChecklistTemplateItemCreate,
  Manual,
  ManualCreate,
  ManualSection,
  ManualSectionCreate,
  ManualStep,
  ManualStepCreate,
  Role,
  StoreOption,
  User,
  UserCreate
} from '../types';

const emptyUser: UserCreate = {
  username: '',
  name: '',
  role: 'operacao',
  password: ''
};

const emptyTemplate: ChecklistTemplateCreate = {
  title: '',
  category: '',
  store: 'Grupo Lia'
};

const emptyTemplateItem: ChecklistTemplateItemCreate = {
  section: '',
  text: ''
};

const emptyManual: ManualCreate = {
  unit: '',
  title: '',
  temperature: '',
  time_standard: '',
  critical_point: '',
  tip: ''
};

const emptyManualSection: ManualSectionCreate = {
  title: ''
};

const emptyManualStep: ManualStepCreate = {
  text: ''
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
  const aiInteractions = useQuery({ queryKey: ['admin-ai-interactions'], queryFn: api.aiInteractions, enabled: isAdmin });

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
          title="Historico IA"
          value={aiInteractions.data?.length ?? 0}
          icon={Bot}
          loading={aiInteractions.isLoading}
        />
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
        <TemplatesAdminSection
          templates={templates.data ?? []}
          stores={stores.data ?? []}
          manualsCount={manuals.data?.length ?? 0}
          loading={templates.isLoading}
        />

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

      <section className="mt-5">
        <AiInteractionsAdminSection interactions={aiInteractions.data ?? []} loading={aiInteractions.isLoading} />
      </section>

      <section className="mt-5">
        <ManualsAdminSection manuals={manuals.data ?? []} stores={stores.data ?? []} loading={manuals.isLoading} />
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

function AiInteractionsAdminSection({
  interactions,
  loading
}: {
  interactions: AiInteraction[];
  loading: boolean;
}) {
  return (
    <div className="surface rounded-lg p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-black text-lia-burgundy">Historico da IA</h3>
          <p className="mt-1 text-sm text-lia-muted">Ultimas perguntas feitas para a Lia, com modo e fontes usadas.</p>
        </div>
        <span className="rounded-lg bg-lia-red/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.16em] text-lia-red">
          Auditoria
        </span>
      </div>

      {loading ? <p className="mt-3 text-sm text-lia-muted">Carregando historico da IA...</p> : null}

      {interactions.length ? (
        <div className="mt-3 grid gap-3 xl:grid-cols-2">
          {interactions.slice(0, 8).map((interaction) => (
            <article key={interaction.id} className="rounded-lg bg-white p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-black text-lia-burgundy">{interaction.user_name ?? `Usuario #${interaction.user_id}`}</p>
                <span className="rounded-lg bg-lia-cream px-2 py-1 text-xs font-bold text-lia-muted">
                  {interaction.response_mode} / {interaction.ai_mode}
                </span>
              </div>
              <p className="mt-2 line-clamp-2 text-sm font-semibold text-lia-ink">{interaction.question}</p>
              <p className="mt-2 line-clamp-2 text-xs leading-5 text-lia-muted">{interaction.answer}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold text-lia-muted">
                <span>{new Date(interaction.created_at).toLocaleString('pt-BR')}</span>
                <span>{interaction.latency_ms} ms</span>
                <span>{interaction.sources.length} fonte(s)</span>
              </div>
              {interaction.error_message ? (
                <p className="mt-2 rounded-lg bg-lia-red/10 px-2 py-1 text-xs font-bold text-lia-red">
                  {interaction.error_message}
                </p>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-lia-muted">Nenhuma interacao com a Lia registrada ainda.</p>
      )}
    </div>
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

function TemplatesAdminSection({
  templates,
  stores,
  manualsCount,
  loading
}: {
  templates: ChecklistTemplate[];
  stores: StoreOption[];
  manualsCount: number;
  loading: boolean;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ChecklistTemplateCreate>(emptyTemplate);

  const createTemplate = useMutation({
    mutationFn: api.createChecklistTemplate,
    onSuccess: () => {
      setForm(emptyTemplate);
      queryClient.invalidateQueries({ queryKey: ['admin-checklist-templates'] });
    }
  });

  const updateTemplate = useMutation({
    mutationFn: ({
      templateId,
      payload
    }: {
      templateId: number;
      payload: Partial<Pick<ChecklistTemplate, 'title' | 'category' | 'store' | 'active'>>;
    }) => api.updateChecklistTemplate(templateId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-checklist-templates'] })
  });

  const createItem = useMutation({
    mutationFn: ({ templateId, payload }: { templateId: number; payload: ChecklistTemplateItemCreate }) =>
      api.createChecklistTemplateItem(templateId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-checklist-templates'] })
  });

  const updateItem = useMutation({
    mutationFn: ({
      itemId,
      payload
    }: {
      itemId: number;
      payload: Partial<Pick<ChecklistTemplateItem, 'section' | 'text' | 'active'>>;
    }) => api.updateChecklistTemplateItem(itemId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-checklist-templates'] })
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createTemplate.mutate(form);
  }

  return (
    <div className="surface rounded-lg p-4">
      <h3 className="text-lg font-black text-lia-burgundy">Templates de checklist</h3>
      <p className="mt-1 text-sm text-lia-muted">{manualsCount} manuais tecnicos cadastrados para consulta.</p>

      <form onSubmit={submit} className="mt-3 grid gap-3 rounded-lg bg-white p-3">
        <div className="grid gap-3 sm:grid-cols-3">
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="Titulo"
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            required
          />
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="Categoria"
            value={form.category}
            onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}
            required
          />
          <select
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            value={form.store}
            onChange={(event) => setForm((current) => ({ ...current, store: event.target.value }))}
          >
            <option>Grupo Lia</option>
            {stores
              .filter((store) => store.active && store.name !== 'Grupo Lia')
              .map((store) => (
                <option key={store.id}>{store.name}</option>
              ))}
          </select>
        </div>
        {createTemplate.error ? <p className="text-sm font-semibold text-lia-red">{createTemplate.error.message}</p> : null}
        <button
          className="focus-ring rounded-lg bg-lia-red px-3 py-2 text-sm font-bold text-white disabled:opacity-60"
          disabled={createTemplate.isPending}
        >
          {createTemplate.isPending ? 'Criando...' : 'Criar template'}
        </button>
      </form>

      <div className="mt-3 space-y-3">
        {loading ? <p className="text-sm text-lia-muted">Carregando templates...</p> : null}
        {templates.map((template) => (
          <TemplateRow
            key={template.id}
            template={template}
            stores={stores}
            onSave={(payload) => updateTemplate.mutate({ templateId: template.id, payload })}
            onCreateItem={(payload) => createItem.mutate({ templateId: template.id, payload })}
            onSaveItem={(itemId, payload) => updateItem.mutate({ itemId, payload })}
          />
        ))}
      </div>
    </div>
  );
}

function TemplateRow({
  template,
  stores,
  onSave,
  onCreateItem,
  onSaveItem
}: {
  template: ChecklistTemplate;
  stores: StoreOption[];
  onSave: (payload: Partial<Pick<ChecklistTemplate, 'title' | 'category' | 'store' | 'active'>>) => void;
  onCreateItem: (payload: ChecklistTemplateItemCreate) => void;
  onSaveItem: (itemId: number, payload: Partial<Pick<ChecklistTemplateItem, 'section' | 'text' | 'active'>>) => void;
}) {
  const [title, setTitle] = useState(template.title);
  const [category, setCategory] = useState(template.category);
  const [store, setStore] = useState(template.store);
  const [itemForm, setItemForm] = useState<ChecklistTemplateItemCreate>(emptyTemplateItem);

  function submitItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onCreateItem(itemForm);
    setItemForm(emptyTemplateItem);
  }

  return (
    <div className="rounded-lg bg-white p-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 px-3 py-2 text-sm font-semibold text-lia-burgundy"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <input
          className="focus-ring w-32 rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        />
        <select
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          value={store}
          onChange={(event) => setStore(event.target.value)}
        >
          <option>Grupo Lia</option>
          {stores
            .filter((storeOption) => storeOption.active && storeOption.name !== 'Grupo Lia')
            .map((storeOption) => (
              <option key={storeOption.id}>{storeOption.name}</option>
            ))}
        </select>
        <StatusPill active={template.active} />
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ title, category, store })}
        >
          Salvar template
        </button>
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ active: !template.active })}
        >
          {template.active ? 'Desativar' : 'Ativar'}
        </button>
      </div>

      <form onSubmit={submitItem} className="mt-3 grid gap-2 rounded-lg bg-lia-cream/60 p-2 sm:grid-cols-[0.35fr_1fr_auto]">
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          placeholder="Secao"
          value={itemForm.section}
          onChange={(event) => setItemForm((current) => ({ ...current, section: event.target.value }))}
          required
        />
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          placeholder="Novo item do checklist"
          value={itemForm.text}
          onChange={(event) => setItemForm((current) => ({ ...current, text: event.target.value }))}
          required
        />
        <button className="focus-ring rounded-lg bg-lia-burgundy px-3 py-2 text-xs font-bold text-white">
          Adicionar
        </button>
      </form>

      <div className="mt-3 space-y-2">
        {template.items.map((item) => (
          <TemplateItemRow key={item.id} item={item} onSave={(payload) => onSaveItem(item.id, payload)} />
        ))}
        {!template.items.length ? <p className="text-sm text-lia-muted">Nenhum item cadastrado neste template.</p> : null}
      </div>
    </div>
  );
}

function TemplateItemRow({
  item,
  onSave
}: {
  item: ChecklistTemplateItem;
  onSave: (payload: Partial<Pick<ChecklistTemplateItem, 'section' | 'text' | 'active'>>) => void;
}) {
  const [section, setSection] = useState(item.section);
  const [text, setText] = useState(item.text);

  return (
    <div className="rounded-lg border border-lia-red/10 bg-lia-cream/40 p-2">
      <div className="grid gap-2 sm:grid-cols-[0.3fr_1fr_auto]">
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-xs"
          value={section}
          onChange={(event) => setSection(event.target.value)}
        />
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-xs"
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <StatusPill active={item.active} />
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ section, text })}
        >
          Salvar item
        </button>
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ active: !item.active })}
        >
          {item.active ? 'Desativar' : 'Ativar'}
        </button>
      </div>
    </div>
  );
}

function ManualsAdminSection({
  manuals,
  stores,
  loading
}: {
  manuals: Manual[];
  stores: StoreOption[];
  loading: boolean;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ManualCreate>(emptyManual);

  const createManual = useMutation({
    mutationFn: api.createManual,
    onSuccess: () => {
      setForm(emptyManual);
      queryClient.invalidateQueries({ queryKey: ['admin-manuals'] });
      queryClient.invalidateQueries({ queryKey: ['manuals'] });
    }
  });

  const updateManual = useMutation({
    mutationFn: ({ manualId, payload }: { manualId: number; payload: Partial<ManualCreate> & { active?: boolean } }) =>
      api.updateManual(manualId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-manuals'] });
      queryClient.invalidateQueries({ queryKey: ['manuals'] });
    }
  });

  const createSection = useMutation({
    mutationFn: ({ manualId, payload }: { manualId: number; payload: ManualSectionCreate }) =>
      api.createManualSection(manualId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-manuals'] });
      queryClient.invalidateQueries({ queryKey: ['manuals'] });
    }
  });

  const updateSection = useMutation({
    mutationFn: ({ sectionId, payload }: { sectionId: number; payload: Partial<Pick<ManualSection, 'title' | 'active'>> }) =>
      api.updateManualSection(sectionId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-manuals'] });
      queryClient.invalidateQueries({ queryKey: ['manuals'] });
    }
  });

  const createStep = useMutation({
    mutationFn: ({ sectionId, payload }: { sectionId: number; payload: ManualStepCreate }) =>
      api.createManualStep(sectionId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-manuals'] });
      queryClient.invalidateQueries({ queryKey: ['manuals'] });
    }
  });

  const updateStep = useMutation({
    mutationFn: ({ stepId, payload }: { stepId: number; payload: Partial<Pick<ManualStep, 'text' | 'active'>> }) =>
      api.updateManualStep(stepId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-manuals'] });
      queryClient.invalidateQueries({ queryKey: ['manuals'] });
    }
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createManual.mutate(form);
  }

  return (
    <div className="surface rounded-lg p-4">
      <h3 className="text-lg font-black text-lia-burgundy">Manuais operacionais</h3>
      <p className="mt-1 text-sm text-lia-muted">Conteudo usado pela tela de manuais e pela Lia.</p>

      <form onSubmit={submit} className="mt-3 grid gap-3 rounded-lg bg-white p-3">
        <div className="grid gap-3 md:grid-cols-3">
          <select
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            value={form.unit}
            onChange={(event) => setForm((current) => ({ ...current, unit: event.target.value }))}
            required
          >
            <option value="">Unidade</option>
            {stores
              .filter((store) => store.active && store.name !== 'Grupo Lia')
              .map((store) => (
                <option key={store.id}>{store.name}</option>
              ))}
          </select>
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="Titulo"
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            required
          />
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="Temperatura"
            value={form.temperature}
            onChange={(event) => setForm((current) => ({ ...current, temperature: event.target.value }))}
            required
          />
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="Tempo padrao"
            value={form.time_standard}
            onChange={(event) => setForm((current) => ({ ...current, time_standard: event.target.value }))}
            required
          />
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="Ponto critico"
            value={form.critical_point}
            onChange={(event) => setForm((current) => ({ ...current, critical_point: event.target.value }))}
            required
          />
          <input
            className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
            placeholder="Dica"
            value={form.tip}
            onChange={(event) => setForm((current) => ({ ...current, tip: event.target.value }))}
            required
          />
        </div>
        {createManual.error ? <p className="text-sm font-semibold text-lia-red">{createManual.error.message}</p> : null}
        <button
          className="focus-ring rounded-lg bg-lia-red px-3 py-2 text-sm font-bold text-white disabled:opacity-60"
          disabled={createManual.isPending}
        >
          {createManual.isPending ? 'Criando...' : 'Criar manual'}
        </button>
      </form>

      <div className="mt-3 grid gap-3 xl:grid-cols-2">
        {loading ? <p className="text-sm text-lia-muted">Carregando manuais...</p> : null}
        {manuals.map((manual) => (
          <ManualRow
            key={manual.id}
            manual={manual}
            stores={stores}
            onSave={(payload) => updateManual.mutate({ manualId: manual.id, payload })}
            onCreateSection={(payload) => createSection.mutate({ manualId: manual.id, payload })}
            onSaveSection={(sectionId, payload) => updateSection.mutate({ sectionId, payload })}
            onCreateStep={(sectionId, payload) => createStep.mutate({ sectionId, payload })}
            onSaveStep={(stepId, payload) => updateStep.mutate({ stepId, payload })}
          />
        ))}
      </div>
    </div>
  );
}

function ManualRow({
  manual,
  stores,
  onSave,
  onCreateSection,
  onSaveSection,
  onCreateStep,
  onSaveStep
}: {
  manual: Manual;
  stores: StoreOption[];
  onSave: (payload: Partial<ManualCreate> & { active?: boolean }) => void;
  onCreateSection: (payload: ManualSectionCreate) => void;
  onSaveSection: (sectionId: number, payload: Partial<Pick<ManualSection, 'title' | 'active'>>) => void;
  onCreateStep: (sectionId: number, payload: ManualStepCreate) => void;
  onSaveStep: (stepId: number, payload: Partial<Pick<ManualStep, 'text' | 'active'>>) => void;
}) {
  const [unit, setUnit] = useState(manual.unit);
  const [title, setTitle] = useState(manual.title);
  const [temperature, setTemperature] = useState(manual.temperature);
  const [timeStandard, setTimeStandard] = useState(manual.time_standard);
  const [criticalPoint, setCriticalPoint] = useState(manual.critical_point);
  const [tip, setTip] = useState(manual.tip);
  const [sectionForm, setSectionForm] = useState<ManualSectionCreate>(emptyManualSection);

  function submitSection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onCreateSection(sectionForm);
    setSectionForm(emptyManualSection);
  }

  return (
    <div className="rounded-lg bg-white p-3">
      <div className="grid gap-2 md:grid-cols-2">
        <select
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          value={unit}
          onChange={(event) => setUnit(event.target.value)}
        >
          {stores
            .filter((store) => store.active && store.name !== 'Grupo Lia')
            .map((store) => (
              <option key={store.id}>{store.name}</option>
            ))}
        </select>
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm font-semibold text-lia-burgundy"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          value={temperature}
          onChange={(event) => setTemperature(event.target.value)}
        />
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          value={timeStandard}
          onChange={(event) => setTimeStandard(event.target.value)}
        />
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          value={criticalPoint}
          onChange={(event) => setCriticalPoint(event.target.value)}
        />
        <input
          className="focus-ring rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          value={tip}
          onChange={(event) => setTip(event.target.value)}
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <StatusPill active={manual.active} />
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() =>
            onSave({
              unit,
              title,
              temperature,
              time_standard: timeStandard,
              critical_point: criticalPoint,
              tip
            })
          }
        >
          Salvar manual
        </button>
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ active: !manual.active })}
        >
          {manual.active ? 'Desativar' : 'Ativar'}
        </button>
      </div>

      <form onSubmit={submitSection} className="mt-3 flex gap-2 rounded-lg bg-lia-cream/60 p-2">
        <input
          className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 px-3 py-2 text-sm"
          placeholder="Nova secao"
          value={sectionForm.title}
          onChange={(event) => setSectionForm({ title: event.target.value })}
          required
        />
        <button className="focus-ring rounded-lg bg-lia-burgundy px-3 py-2 text-xs font-bold text-white">
          Adicionar
        </button>
      </form>

      <div className="mt-3 space-y-2">
        {manual.sections.map((section) => (
          <ManualSectionRow
            key={section.id}
            section={section}
            onSave={(payload) => onSaveSection(section.id, payload)}
            onCreateStep={(payload) => onCreateStep(section.id, payload)}
            onSaveStep={onSaveStep}
          />
        ))}
        {!manual.sections.length ? <p className="text-sm text-lia-muted">Nenhuma secao cadastrada neste manual.</p> : null}
      </div>
    </div>
  );
}

function ManualSectionRow({
  section,
  onSave,
  onCreateStep,
  onSaveStep
}: {
  section: ManualSection;
  onSave: (payload: Partial<Pick<ManualSection, 'title' | 'active'>>) => void;
  onCreateStep: (payload: ManualStepCreate) => void;
  onSaveStep: (stepId: number, payload: Partial<Pick<ManualStep, 'text' | 'active'>>) => void;
}) {
  const [title, setTitle] = useState(section.title);
  const [stepForm, setStepForm] = useState<ManualStepCreate>(emptyManualStep);

  function submitStep(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onCreateStep(stepForm);
    setStepForm(emptyManualStep);
  }

  return (
    <div className="rounded-lg border border-lia-red/10 bg-lia-cream/50 p-2">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 px-3 py-2 text-sm font-semibold text-lia-burgundy"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <StatusPill active={section.active} />
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ title })}
        >
          Salvar secao
        </button>
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ active: !section.active })}
        >
          {section.active ? 'Desativar' : 'Ativar'}
        </button>
      </div>

      <form onSubmit={submitStep} className="mt-2 flex gap-2">
        <input
          className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 px-3 py-2 text-xs"
          placeholder="Novo passo"
          value={stepForm.text}
          onChange={(event) => setStepForm({ text: event.target.value })}
          required
        />
        <button className="focus-ring rounded-lg bg-lia-burgundy px-3 py-2 text-xs font-bold text-white">
          Adicionar
        </button>
      </form>

      <div className="mt-2 space-y-2">
        {section.steps.map((step) => (
          <ManualStepRow key={step.id} step={step} onSave={(payload) => onSaveStep(step.id, payload)} />
        ))}
      </div>
    </div>
  );
}

function ManualStepRow({
  step,
  onSave
}: {
  step: ManualStep;
  onSave: (payload: Partial<Pick<ManualStep, 'text' | 'active'>>) => void;
}) {
  const [text, setText] = useState(step.text);

  return (
    <div className="rounded-lg bg-white p-2">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="focus-ring min-w-0 flex-1 rounded-lg border border-lia-red/15 px-3 py-2 text-xs"
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <StatusPill active={step.active} />
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ text })}
        >
          Salvar passo
        </button>
        <button
          className="focus-ring rounded-lg border border-lia-red/20 px-3 py-2 text-xs font-bold text-lia-burgundy"
          onClick={() => onSave({ active: !step.active })}
        >
          {step.active ? 'Desativar' : 'Ativar'}
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
