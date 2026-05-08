from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserRead(BaseModel):
    id: int
    username: str
    name: str
    role: str

    model_config = {"from_attributes": True}


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
