export type Role = 'admin' | 'lideranca' | 'gerente' | 'operacao' | 'auditor';

export interface User {
  id: number;
  username: string;
  name: string;
  role: Role;
  store_id: number | null;
  store_name: string | null;
  active: boolean;
}

export interface UserCreate {
  username: string;
  name: string;
  role: Role;
  store_id?: number | null;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  user: User;
}

export type LeadershipRecordType = 'feedback' | 'advertencia' | 'suspensao' | 'demissao';

export interface LeadershipTokenResponse {
  access_token: string;
  token_type: 'bearer';
  area: 'leadership';
}

export interface LeadershipEmployee {
  id: number;
  name: string;
  store: string;
  position: string | null;
  active: boolean;
  created_at: string;
  record_count: number;
}

export interface LeadershipEmployeeCreate {
  name: string;
  store: string;
  position?: string;
}

export interface LeadershipEmployeeUpdate {
  name?: string;
  store?: string;
  position?: string | null;
  active?: boolean;
}

export interface LeadershipRecord {
  id: number;
  employee_id: number;
  employee_name: string;
  employee_store: string;
  record_type: LeadershipRecordType;
  description: string;
  applied_at: string;
  created_at: string;
  created_by: string;
}

export interface LeadershipRecordCreate {
  record_type: LeadershipRecordType;
  description: string;
  applied_at?: string;
}

export interface ManualStep {
  id: number;
  text: string;
  position: number;
  active: boolean;
}

export interface ManualSection {
  id: number;
  title: string;
  position: number;
  active: boolean;
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
  active: boolean;
  sections: ManualSection[];
}

export interface ManualCreate {
  unit: string;
  title: string;
  temperature: string;
  time_standard: string;
  critical_point: string;
  tip: string;
}

export interface ManualSectionCreate {
  title: string;
}

export interface ManualStepCreate {
  text: string;
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

export interface StoreOption {
  id: number;
  name: string;
  active: boolean;
}

export interface ChecklistTemplateItem {
  id: number;
  section: string;
  text: string;
  position: number;
  active: boolean;
}

export interface ChecklistTemplate {
  id: number;
  title: string;
  category: string;
  store: string;
  active: boolean;
  items: ChecklistTemplateItem[];
}

export interface ChecklistTemplateCreate {
  title: string;
  category: string;
  store: string;
}

export interface ChecklistTemplateItemCreate {
  section: string;
  text: string;
}

export type IncidentCategory =
  | 'estoque'
  | 'limpeza'
  | 'equipamento'
  | 'atendimento'
  | 'delivery'
  | 'caixa'
  | 'validade'
  | 'outro';

export type IncidentSeverity = 'baixa' | 'media' | 'alta' | 'critica';
export type IncidentStatus = 'aberta' | 'em_andamento' | 'resolvida' | 'cancelada';

export interface OperationalIncident {
  id: number;
  store: string;
  category: IncidentCategory;
  severity: IncidentSeverity;
  description: string;
  status: IncidentStatus;
  created_by: string | null;
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
}

export interface OperationalIncidentCreate {
  store: string;
  category: IncidentCategory;
  severity: IncidentSeverity;
  description: string;
}

export interface ChecklistEvidence {
  id: number;
  checklist_run_item_id: number;
  uploaded_by: string | null;
  storage_provider: string;
  file_url: string | null;
  original_filename: string;
  content_type: string;
  file_size: number;
  created_at: string;
  run_id: number | null;
  store: string | null;
  checklist_title: string | null;
  item_text: string | null;
}

export interface ReportSummary {
  start_date: string;
  end_date: string;
  store: string | null;
  total_checklists: number;
  total_items: number;
  completed_items: number;
  completion_percent: number;
  pending_tasks: number;
  total_incidents: number;
  incidents_by_status: Record<string, number>;
  incidents_by_severity: Record<string, number>;
  incidents_by_category: Record<string, number>;
  evidences_uploaded: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export type AiResponseMode = 'rapido' | 'detalhado' | 'treinamento';
export type AiMode = 'offline' | 'gemini' | 'error';

export interface ChatSource {
  source_type: string;
  manual_id: number;
  unit: string;
  manual_title: string;
  title: string | null;
  section_title: string | null;
  excerpt: string;
}

export interface ChatResponse {
  reply: string;
  mode: AiMode;
  session_id: number;
  sources: ChatSource[];
  needs_manager_confirmation: boolean;
  response_mode: AiResponseMode;
}

export interface AiStatus {
  configured: boolean;
  key_length: number;
  key_fingerprint: string | null;
  model: string;
}

export interface AiChatHistoryItem {
  id: number;
  session_id: number;
  store: string;
  unit: string | null;
  question: string;
  answer_summary: string;
  sources: ChatSource[];
  mode: AiMode;
  needs_manager_confirmation: boolean;
  created_at: string;
}

export interface AiInteraction {
  id: number;
  user_id: number;
  user_name: string | null;
  question: string;
  answer: string;
  response_mode: AiResponseMode;
  ai_mode: AiMode;
  sources: ChatSource[];
  created_at: string;
  error_message: string | null;
  latency_ms: number;
}
