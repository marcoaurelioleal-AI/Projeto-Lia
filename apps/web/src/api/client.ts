import type {
  AiChatHistoryItem,
  AiStatus,
  ChatMessage,
  ChatResponse,
  ChecklistEvidence,
  ChecklistRun,
  ChecklistTemplate,
  IncidentStatus,
  LoginResponse,
  Manual,
  OperationalIncident,
  OperationalIncidentCreate,
  ReportSummary,
  StoreOption,
  User,
  UserCreate
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';
const TOKEN_KEY = 'lia_access_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? 'Não foi possível completar a solicitação.');
  }

  return response.json() as Promise<T>;
}

function withParams(path: string, params: Record<string, string | number | null | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export async function fetchEvidenceBlob(path: string): Promise<Blob> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  });
  if (!response.ok) {
    throw new Error('Nao foi possivel carregar a evidencia.');
  }
  return response.blob();
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),
  me: () => request<User>('/auth/me'),
  manuals: () => request<Manual[]>('/manuals'),
  checklists: (runDate: string, store = 'Grupo Lia') =>
    request<ChecklistRun[]>(`/checklists?run_date=${runDate}&store=${encodeURIComponent(store)}`),
  updateChecklistItem: (runId: number, itemId: number, done: boolean) =>
    request<ChecklistRun>(`/checklists/${runId}/items`, {
      method: 'PATCH',
      body: JSON.stringify({ item_id: itemId, done })
    }),
  updateClosingNote: (runId: number, closingNote: string) =>
    request<ChecklistRun>(`/checklists/${runId}/closing-note`, {
      method: 'PATCH',
      body: JSON.stringify({ closing_note: closingNote })
    }),
  chat: (messages: ChatMessage[], options: { store?: string; unit?: string; sessionId?: number | null } = {}) =>
    request<ChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages,
        store: options.store,
        unit: options.unit || undefined,
        session_id: options.sessionId ?? undefined
      })
    }),
  aiHistory: () => request<AiChatHistoryItem[]>('/ai/history'),
  aiStatus: () => request<AiStatus>('/ai/status'),
  adminUsers: () => request<User[]>('/admin/users'),
  createAdminUser: (payload: UserCreate) =>
    request<User>('/admin/users', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateAdminUser: (userId: number, payload: Partial<Pick<User, 'name' | 'role' | 'active'>>) =>
    request<User>(`/admin/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  deactivateAdminUser: (userId: number) =>
    request<User>(`/admin/users/${userId}`, {
      method: 'DELETE'
    }),
  adminStores: () => request<StoreOption[]>('/admin/stores'),
  createAdminStore: (name: string) =>
    request<StoreOption>('/admin/stores', {
      method: 'POST',
      body: JSON.stringify({ name })
    }),
  updateAdminStore: (storeId: number, payload: Partial<Pick<StoreOption, 'name' | 'active'>>) =>
    request<StoreOption>(`/admin/stores/${storeId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  deactivateAdminStore: (storeId: number) =>
    request<StoreOption>(`/admin/stores/${storeId}`, {
      method: 'DELETE'
    }),
  adminChecklistTemplates: () => request<ChecklistTemplate[]>('/admin/checklist-templates'),
  adminManuals: () => request<Manual[]>('/admin/manuals'),
  incidents: (options: { status?: IncidentStatus | 'todas'; store?: string } = {}) =>
    request<OperationalIncident[]>(
      withParams('/incidents', {
        status: options.status === 'todas' ? undefined : options.status,
        store: options.store
      })
    ),
  createIncident: (payload: OperationalIncidentCreate) =>
    request<OperationalIncident>('/incidents', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateIncident: (incidentId: number, payload: Partial<OperationalIncidentCreate> & { status?: IncidentStatus }) =>
    request<OperationalIncident>(`/incidents/${incidentId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  reportSummary: (options: { startDate: string; endDate: string; store?: string }) =>
    request<ReportSummary>(
      withParams('/reports/summary', {
        start_date: options.startDate,
        end_date: options.endDate,
        store: options.store
      })
    ),
  uploadChecklistEvidence: (itemId: number, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<ChecklistEvidence>(`/checklists/items/${itemId}/evidences`, {
      method: 'POST',
      body: form
    });
  },
  checklistItemEvidences: (itemId: number) =>
    request<ChecklistEvidence[]>(`/checklists/items/${itemId}/evidences`),
  checklistRunEvidences: (runId: number) => request<ChecklistEvidence[]>(`/checklists/${runId}/evidences`),
  evidenceAudit: (options: { store?: string; startDate?: string; endDate?: string } = {}) =>
    request<ChecklistEvidence[]>(
      withParams('/evidences', {
        store: options.store,
        start_date: options.startDate,
        end_date: options.endDate
      })
    )
};
