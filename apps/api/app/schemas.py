from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["admin", "lideranca", "gerente", "operacao", "auditor"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserRead(BaseModel):
    id: int
    username: str
    name: str
    role: Role
    store_id: int | None = None
    store_name: str | None = None
    active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=2, max_length=120)
    role: Role = "operacao"
    store_id: int | None = None
    password: str = Field(min_length=6, max_length=200)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: Role | None = None
    store_id: int | None = None
    active: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LeadershipTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    area: str = "leadership"


LeadershipRecordType = Literal["feedback", "advertencia", "suspensao", "demissao"]


class LeadershipEmployeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    store: str = Field(default="Grupo Lia", min_length=1, max_length=80)
    position: str | None = Field(default=None, max_length=120)


class LeadershipEmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    store: str | None = Field(default=None, min_length=1, max_length=80)
    position: str | None = Field(default=None, max_length=120)
    active: bool | None = None


class LeadershipEmployeeRead(BaseModel):
    id: int
    name: str
    store: str
    position: str | None = None
    active: bool
    created_at: datetime
    record_count: int = 0


class LeadershipRecordCreate(BaseModel):
    record_type: LeadershipRecordType
    description: str = Field(min_length=1, max_length=4000)
    applied_at: date | None = None


class LeadershipRecordRead(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    employee_store: str
    record_type: str
    description: str
    applied_at: date
    created_at: datetime
    created_by: str


class ManualStepRead(BaseModel):
    id: int
    text: str
    position: int
    active: bool

    model_config = {"from_attributes": True}


class ManualStepCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1200)


class ManualStepUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=1200)
    active: bool | None = None


class ManualSectionRead(BaseModel):
    id: int
    title: str
    position: int
    active: bool
    steps: list[ManualStepRead]

    model_config = {"from_attributes": True}


class ManualSectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class ManualSectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    active: bool | None = None


class ManualRead(BaseModel):
    id: int
    unit: str
    title: str
    temperature: str
    time_standard: str
    critical_point: str
    tip: str
    active: bool
    sections: list[ManualSectionRead]

    model_config = {"from_attributes": True}


class ManualCreate(BaseModel):
    unit: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=180)
    temperature: str = Field(min_length=1, max_length=120)
    time_standard: str = Field(min_length=1, max_length=120)
    critical_point: str = Field(min_length=1, max_length=180)
    tip: str = Field(min_length=1, max_length=1500)


class ManualUpdate(BaseModel):
    unit: str | None = Field(default=None, min_length=2, max_length=80)
    title: str | None = Field(default=None, min_length=2, max_length=180)
    temperature: str | None = Field(default=None, min_length=1, max_length=120)
    time_standard: str | None = Field(default=None, min_length=1, max_length=120)
    critical_point: str | None = Field(default=None, min_length=1, max_length=180)
    tip: str | None = Field(default=None, min_length=1, max_length=1500)
    active: bool | None = None


class ChecklistItemRead(BaseModel):
    id: int
    section: str
    text: str
    done: bool
    completed_at: datetime | None = None
    completed_by: str | None = None


class ChecklistRunRead(BaseModel):
    id: int
    title: str
    category: str
    store: str
    run_date: date
    progress: int
    completed: int
    total: int
    closing_note: str | None = None
    items: list[ChecklistItemRead]


class ChecklistItemUpdate(BaseModel):
    item_id: int
    done: bool


class ClosingNoteUpdate(BaseModel):
    closing_note: str = Field(max_length=1500)


IncidentCategory = Literal[
    "estoque",
    "limpeza",
    "equipamento",
    "atendimento",
    "delivery",
    "caixa",
    "validade",
    "outro",
]
IncidentSeverity = Literal["baixa", "media", "alta", "critica"]
IncidentStatus = Literal["aberta", "em_andamento", "resolvida", "cancelada"]
AiResponseMode = Literal["rapido", "detalhado", "treinamento"]
AiMode = Literal["gemini", "offline", "error"]
AiFeedbackRating = Literal["ajudou", "nao_ajudou"]


class OperationalIncidentCreate(BaseModel):
    store: str = Field(default="Grupo Lia", min_length=1, max_length=80)
    category: IncidentCategory
    severity: IncidentSeverity
    description: str = Field(min_length=1, max_length=3000)


class OperationalIncidentUpdate(BaseModel):
    store: str | None = Field(default=None, min_length=1, max_length=80)
    category: IncidentCategory | None = None
    severity: IncidentSeverity | None = None
    description: str | None = Field(default=None, min_length=1, max_length=3000)
    status: IncidentStatus | None = None


class OperationalIncidentRead(BaseModel):
    id: int
    store: str
    category: str
    severity: str
    description: str
    status: str
    created_by: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class ChecklistEvidenceRead(BaseModel):
    id: int
    checklist_run_item_id: int
    uploaded_by: str | None = None
    storage_provider: str
    file_url: str | None = None
    original_filename: str
    content_type: str
    file_size: int
    created_at: datetime
    run_id: int | None = None
    store: str | None = None
    checklist_title: str | None = None
    item_text: str | None = None


class EvidenceAuditFilterOptionsRead(BaseModel):
    stores: list[str]
    checklists: list[str]
    users: list[str]


class StoreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    active: bool | None = None


class StoreRead(BaseModel):
    id: int
    name: str
    active: bool

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    id: int
    action: str
    actor_user_id: int | None = None
    actor_username: str | None = None
    actor_role: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    store: str | None = None
    status: str
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestMetricsRead(BaseModel):
    total_requests: int
    error_requests: int
    average_latency_ms: float
    p95_latency_ms: float
    by_status: dict[str, int]
    by_path: dict[str, int]
    last_request_at: datetime | None = None


class ObservabilityStatusRead(BaseModel):
    status: str
    service: str
    environment: str
    database: str
    storage_provider: str
    started_at: datetime
    request_metrics: RequestMetricsRead


class ChecklistTemplateItemRead(BaseModel):
    id: int
    section: str
    text: str
    position: int
    active: bool

    model_config = {"from_attributes": True}


class ChecklistTemplateItemCreate(BaseModel):
    section: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=1200)


class ChecklistTemplateItemUpdate(BaseModel):
    section: str | None = Field(default=None, min_length=1, max_length=120)
    text: str | None = Field(default=None, min_length=1, max_length=1200)
    active: bool | None = None


class ChecklistTemplateRead(BaseModel):
    id: int
    title: str
    category: str
    store: str
    active: bool
    items: list[ChecklistTemplateItemRead] = []

    model_config = {"from_attributes": True}


class ChecklistTemplateCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=80)
    store: str = Field(default="Grupo Lia", min_length=1, max_length=80)


class ChecklistTemplateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    store: str | None = Field(default=None, min_length=1, max_length=80)
    active: bool | None = None


class ReportSummaryRead(BaseModel):
    start_date: date
    end_date: date
    store: str | None = None
    total_checklists: int
    total_items: int
    completed_items: int
    completion_percent: int
    pending_tasks: int
    total_incidents: int
    incidents_by_status: dict[str, int]
    incidents_by_severity: dict[str, int]
    incidents_by_category: dict[str, int]
    evidences_uploaded: int


class StorePendingSummaryRead(BaseModel):
    store: str
    total_checklists: int
    total_items: int
    completed_items: int
    pending_tasks: int
    completion_percent: int


class ExecutiveDashboardRead(BaseModel):
    today: date
    visible_stores: list[str]
    summary_7d: ReportSummaryRead
    summary_30d: ReportSummaryRead
    store_rankings: list[StorePendingSummaryRead]
    critical_incidents: list[OperationalIncidentRead]
    recent_evidences: list[ChecklistEvidenceRead]


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=2000)


class ChatSource(BaseModel):
    source_type: str = "manual"
    manual_id: int
    unit: str
    manual_title: str
    title: str | None = None
    section_title: str | None = None
    excerpt: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=10)
    store: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, max_length=80)
    session_id: int | None = None
    response_mode: AiResponseMode = "rapido"


class ChatResponse(BaseModel):
    reply: str
    mode: str
    session_id: int
    interaction_id: int
    sources: list[ChatSource] = []
    needs_manager_confirmation: bool = False
    response_mode: AiResponseMode = "rapido"


class AiChatHistoryItem(BaseModel):
    id: int
    session_id: int
    store: str
    unit: str | None = None
    question: str
    answer_summary: str
    sources: list[ChatSource] = []
    mode: str
    needs_manager_confirmation: bool
    created_at: datetime


class AiInteractionRead(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    question: str
    answer: str
    response_mode: str
    ai_mode: str
    sources: list[ChatSource] = []
    created_at: datetime
    error_message: str | None = None
    latency_ms: int
    needs_manager_confirmation: bool = False
    feedback_rating: AiFeedbackRating | None = None
    feedback_comment: str | None = None
    feedback_created_at: datetime | None = None


class AiFeedbackCreate(BaseModel):
    rating: AiFeedbackRating
    comment: str | None = Field(default=None, max_length=1200)


class AiKnowledgeGapRead(BaseModel):
    question: str
    occurrences: int
    negative_feedback_count: int
    needs_manager_confirmation_count: int
    last_seen_at: datetime
    suggested_manual_update: str
    sample_sources: list[ChatSource] = []


class HealthResponse(BaseModel):
    status: str
    service: str
