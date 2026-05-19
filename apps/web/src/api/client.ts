import type {
  AiChatHistoryItem,
  AiFeedbackRating,
  AiInteraction,
  AiKnowledgeGap,
  AiResponseMode,
  AiStatus,
  AuditLog,
  ChatMessage,
  ChatResponse,
  ChecklistEvidence,
  ChecklistRun,
  ChecklistTemplate,
  ChecklistTemplateCreate,
  ChecklistTemplateItemCreate,
  EvidenceAuditFilterOptions,
  ExecutiveDashboard,
  IncidentStatus,
  LeadershipEmployee,
  LeadershipEmployeeCreate,
  LeadershipEmployeeUpdate,
  LeadershipRecord,
  LeadershipRecordCreate,
  LeadershipTokenResponse,
  LoginResponse,
  Manual,
  ManualCreate,
  ManualSection,
  ManualSectionCreate,
  ManualStep,
  ManualStepCreate,
  OperationalIncident,
  OperationalIncidentCreate,
  ReportSummary,
  StoreOption,
  User,
  UserCreate
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';
const API_ROOT = `${API_BASE_URL.replace(/\/$/, '')}/api`;
const TOKEN_KEY = 'lia_access_token';
const LEADERSHIP_TOKEN_KEY = 'lia_leadership_token';
const SESSION_FLAG_KEY = 'lia_session_active';
const LEADERSHIP_SESSION_FLAG_KEY = 'lia_leadership_session_active';

export function getToken() {
  return sessionStorage.getItem(SESSION_FLAG_KEY);
}

export function setToken(_token: string) {
  void _token;
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.setItem(SESSION_FLAG_KEY, '1');
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(SESSION_FLAG_KEY);
}

export function getLeadershipToken() {
  return sessionStorage.getItem(LEADERSHIP_SESSION_FLAG_KEY);
}

export function setLeadershipToken(_token: string) {
  void _token;
  localStorage.removeItem(LEADERSHIP_TOKEN_KEY);
  sessionStorage.setItem(LEADERSHIP_SESSION_FLAG_KEY, '1');
}

export function clearLeadershipToken() {
  localStorage.removeItem(LEADERSHIP_TOKEN_KEY);
  sessionStorage.removeItem(LEADERSHIP_SESSION_FLAG_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    credentials: 'include',
    headers
  });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      clearToken();
    }
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? 'Não foi possível completar a solicitação.');
  }

  return response.json() as Promise<T>;
}

async function requestLeadership<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    credentials: 'include',
    headers
  });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      clearLeadershipToken();
    }
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? 'Nao foi possivel completar a solicitacao.');
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
  const response = await fetch(`${API_ROOT}${path}`, {
    credentials: 'include'
  });
  if (!response.ok) {
    throw new Error('Nao foi possivel carregar a evidencia.');
  }
  return response.blob();
}

async function requestBlob(path: string, options: RequestInit = {}): Promise<Blob> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    credentials: 'include'
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? 'Nao foi possivel completar a solicitacao.');
  }
  return response.blob();
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),
  leadershipLogin: (username: string, password: string) =>
    requestLeadership<LeadershipTokenResponse>('/leadership/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),
  logout: () => request<{ status: string }>('/auth/logout', { method: 'POST' }),
  leadershipLogout: () => requestLeadership<{ status: string }>('/leadership/logout', { method: 'POST' }),
  leadershipMe: () => requestLeadership<{ username: string; area: 'leadership' }>('/leadership/me'),
  leadershipEmployees: () => requestLeadership<LeadershipEmployee[]>('/leadership/employees'),
  createLeadershipEmployee: (payload: LeadershipEmployeeCreate) =>
    requestLeadership<LeadershipEmployee>('/leadership/employees', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateLeadershipEmployee: (employeeId: number, payload: LeadershipEmployeeUpdate) =>
    requestLeadership<LeadershipEmployee>(`/leadership/employees/${employeeId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  leadershipRecords: () => requestLeadership<LeadershipRecord[]>('/leadership/records'),
  employeeLeadershipRecords: (employeeId: number) =>
    requestLeadership<LeadershipRecord[]>(`/leadership/employees/${employeeId}/records`),
  createLeadershipRecord: (employeeId: number, payload: LeadershipRecordCreate) =>
    requestLeadership<LeadershipRecord>(`/leadership/employees/${employeeId}/records`, {
      method: 'POST',
      body: JSON.stringify(payload)
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
  chat: (
    messages: ChatMessage[],
    options: { store?: string; unit?: string; sessionId?: number | null; responseMode?: AiResponseMode } = {}
  ) =>
    request<ChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages,
        store: options.store,
        unit: options.unit || undefined,
        session_id: options.sessionId ?? undefined,
        response_mode: options.responseMode ?? 'rapido'
      })
    }),
  aiHistory: () => request<AiChatHistoryItem[]>('/ai/history'),
  aiInteractions: () => request<AiInteraction[]>('/ai/interactions'),
  aiKnowledgeGaps: () => request<AiKnowledgeGap[]>('/ai/knowledge-gaps'),
  submitAiFeedback: (interactionId: number, rating: AiFeedbackRating, comment?: string) =>
    request<AiInteraction>(`/ai/interactions/${interactionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ rating, comment })
    }),
  aiStatus: () => request<AiStatus>('/ai/status'),
  adminUsers: () => request<User[]>('/admin/users'),
  createAdminUser: (payload: UserCreate) =>
    request<User>('/admin/users', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateAdminUser: (userId: number, payload: Partial<Pick<User, 'name' | 'role' | 'store_id' | 'active'>>) =>
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
  createChecklistTemplate: (payload: ChecklistTemplateCreate) =>
    request<ChecklistTemplate>('/admin/checklist-templates', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateChecklistTemplate: (
    templateId: number,
    payload: Partial<Pick<ChecklistTemplate, 'title' | 'category' | 'store' | 'active'>>
  ) =>
    request<ChecklistTemplate>(`/admin/checklist-templates/${templateId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  deactivateChecklistTemplate: (templateId: number) =>
    request<ChecklistTemplate>(`/admin/checklist-templates/${templateId}`, {
      method: 'DELETE'
    }),
  createChecklistTemplateItem: (templateId: number, payload: ChecklistTemplateItemCreate) =>
    request<ChecklistTemplate>(`/admin/checklist-templates/${templateId}/items`, {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateChecklistTemplateItem: (
    itemId: number,
    payload: Partial<Pick<ChecklistTemplate['items'][number], 'section' | 'text' | 'active'>>
  ) =>
    request<ChecklistTemplate>(`/admin/checklist-template-items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  deactivateChecklistTemplateItem: (itemId: number) =>
    request<ChecklistTemplate>(`/admin/checklist-template-items/${itemId}`, {
      method: 'DELETE'
    }),
  adminManuals: () => request<Manual[]>('/admin/manuals'),
  createManual: (payload: ManualCreate) =>
    request<Manual>('/admin/manuals', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateManual: (manualId: number, payload: Partial<ManualCreate> & { active?: boolean }) =>
    request<Manual>(`/admin/manuals/${manualId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  deactivateManual: (manualId: number) =>
    request<Manual>(`/admin/manuals/${manualId}`, {
      method: 'DELETE'
    }),
  createManualSection: (manualId: number, payload: ManualSectionCreate) =>
    request<Manual>(`/admin/manuals/${manualId}/sections`, {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateManualSection: (sectionId: number, payload: Partial<Pick<ManualSection, 'title' | 'active'>>) =>
    request<Manual>(`/admin/manual-sections/${sectionId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  deactivateManualSection: (sectionId: number) =>
    request<Manual>(`/admin/manual-sections/${sectionId}`, {
      method: 'DELETE'
    }),
  createManualStep: (sectionId: number, payload: ManualStepCreate) =>
    request<Manual>(`/admin/manual-sections/${sectionId}/steps`, {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  updateManualStep: (stepId: number, payload: Partial<Pick<ManualStep, 'text' | 'active'>>) =>
    request<Manual>(`/admin/manual-steps/${stepId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  deactivateManualStep: (stepId: number) =>
    request<Manual>(`/admin/manual-steps/${stepId}`, {
      method: 'DELETE'
    }),
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
  executiveDashboard: () => request<ExecutiveDashboard>('/reports/executive'),
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
  evidenceAudit: (
    options: { store?: string; startDate?: string; endDate?: string; checklistTitle?: string; uploadedBy?: string } = {}
  ) =>
    request<ChecklistEvidence[]>(
      withParams('/evidences', {
        store: options.store,
        start_date: options.startDate,
        end_date: options.endDate,
        checklist_title: options.checklistTitle,
        uploaded_by: options.uploadedBy
      })
    ),
  evidenceAuditFilterOptions: () => request<EvidenceAuditFilterOptions>('/evidences/filter-options'),
  evidenceAuditExport: (
    options: { store?: string; startDate?: string; endDate?: string; checklistTitle?: string; uploadedBy?: string } = {}
  ) =>
    requestBlob(
      withParams('/evidences/export', {
        store: options.store,
        start_date: options.startDate,
        end_date: options.endDate,
        checklist_title: options.checklistTitle,
        uploaded_by: options.uploadedBy
      })
    ),
  auditLogs: (options: { action?: string; status?: string; entityType?: string; store?: string; limit?: number } = {}) =>
    request<AuditLog[]>(
      withParams('/audit/logs', {
        action: options.action,
        status: options.status,
        entity_type: options.entityType,
        store: options.store,
        limit: options.limit
      })
    )
};
