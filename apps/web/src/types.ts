export type Role = 'admin' | 'operacao';

export interface User {
  id: number;
  username: string;
  name: string;
  role: Role;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  user: User;
}

export interface ManualStep {
  id: number;
  text: string;
  position: number;
}

export interface ManualSection {
  id: number;
  title: string;
  position: number;
  steps: ManualStep[];
}

export interface Manual {
  id: number;
  unit: string;
  title: string;
  temperature: string;
  time_standard: string;
  critical_point: string;
  tip: string;
  sections: ManualSection[];
}

export interface ChecklistItem {
  id: number;
  section: string;
  text: string;
  done: boolean;
  completed_at: string | null;
  completed_by: string | null;
}

export interface ChecklistRun {
  id: number;
  title: string;
  category: string;
  store: string;
  run_date: string;
  progress: number;
  completed: number;
  total: number;
  closing_note: string | null;
  items: ChecklistItem[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
  mode: 'offline' | 'gemini' | 'error';
}

export interface AiStatus {
  configured: boolean;
  key_length: number;
  key_fingerprint: string | null;
  model: string;
}
