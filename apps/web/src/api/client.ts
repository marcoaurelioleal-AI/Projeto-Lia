import type { AiStatus, ChatMessage, ChatResponse, ChecklistRun, LoginResponse, Manual, User } from '../types';

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
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? 'Não foi possível completar a solicitação.');
  }

  return response.json() as Promise<T>;
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
  chat: (messages: ChatMessage[]) =>
    request<ChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ messages })
    }),
  aiStatus: () => request<AiStatus>('/ai/status')
};
