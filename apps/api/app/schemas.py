from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserRead(BaseModel):
    id: int
    username: str
    name: str
    role: str
    active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=2, max_length=120)
    role: Literal["admin", "operacao"] = "operacao"
    password: str = Field(min_length=6, max_length=200)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: Literal["admin", "operacao"] | None = None
    active: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ManualStepRead(BaseModel):
    id: int
    text: str
    position: int

    model_config = {"from_attributes": True}


class ManualSectionRead(BaseModel):
    id: int
    title: str
    position: int
    steps: list[ManualStepRead]

    model_config = {"from_attributes": True}


class ManualRead(BaseModel):
    id: int
    unit: str
    title: str
    temperature: str
    time_standard: str
    critical_point: str
    tip: str
    sections: list[ManualSectionRead]

    model_config = {"from_attributes": True}


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


class ChecklistTemplateItemRead(BaseModel):
    id: int
    section: str
    text: str
    position: int

    model_config = {"from_attributes": True}


class ChecklistTemplateRead(BaseModel):
    id: int
    title: str
    category: str
    store: str
    items: list[ChecklistTemplateItemRead] = []

    model_config = {"from_attributes": True}


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


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class ChatSource(BaseModel):
    manual_id: int
    unit: str
    manual_title: str
    section_title: str | None = None
    excerpt: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=12)
    store: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, max_length=80)
    session_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    mode: str
    session_id: int
    sources: list[ChatSource] = []
    needs_manager_confirmation: bool = False


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


class HealthResponse(BaseModel):
    status: str
    service: str
