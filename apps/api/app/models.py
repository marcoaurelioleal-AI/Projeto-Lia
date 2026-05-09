from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(30), default="operacao")
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Manual(Base):
    __tablename__ = "manuals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    temperature: Mapped[str] = mapped_column(String(120))
    time_standard: Mapped[str] = mapped_column(String(120))
    critical_point: Mapped[str] = mapped_column(String(180))
    tip: Mapped[str] = mapped_column(Text)
    sections: Mapped[list["ManualSection"]] = relationship(
        back_populates="manual", cascade="all, delete-orphan", order_by="ManualSection.position"
    )


class ManualSection(Base):
    __tablename__ = "manual_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manual_id: Mapped[int] = mapped_column(ForeignKey("manuals.id"))
    title: Mapped[str] = mapped_column(String(160))
    position: Mapped[int] = mapped_column(Integer, default=0)
    manual: Mapped[Manual] = relationship(back_populates="sections")
    steps: Mapped[list["ManualStep"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="ManualStep.position"
    )


class ManualStep(Base):
    __tablename__ = "manual_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("manual_sections.id"))
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    section: Mapped[ManualSection] = relationship(back_populates="steps")


class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), unique=True)
    category: Mapped[str] = mapped_column(String(80))
    store: Mapped[str] = mapped_column(String(80), default="Grupo Lia")
    items: Mapped[list["ChecklistTemplateItem"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="ChecklistTemplateItem.position"
    )


class ChecklistTemplateItem(Base):
    __tablename__ = "checklist_template_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("checklist_templates.id"))
    section: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    template: Mapped[ChecklistTemplate] = relationship(back_populates="items")


class ChecklistRun(Base):
    __tablename__ = "checklist_runs"
    __table_args__ = (UniqueConstraint("template_id", "run_date", "store", name="uq_template_date_store"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("checklist_templates.id"))
    run_date: Mapped[date] = mapped_column(Date, index=True)
    store: Mapped[str] = mapped_column(String(80), default="Grupo Lia")
    assigned_to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    closing_note: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    template: Mapped[ChecklistTemplate] = relationship()
    assigned_to: Mapped[User] = relationship()
    items: Mapped[list["ChecklistRunItem"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="ChecklistRunItem.id"
    )


class ChecklistRunItem(Base):
    __tablename__ = "checklist_run_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("checklist_runs.id"))
    template_item_id: Mapped[int] = mapped_column(ForeignKey("checklist_template_items.id"))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    run: Mapped[ChecklistRun] = relationship(back_populates="items")
    template_item: Mapped[ChecklistTemplateItem] = relationship()
    completed_by: Mapped[User] = relationship()
    evidences: Mapped[list["ChecklistEvidence"]] = relationship(
        back_populates="checklist_run_item", cascade="all, delete-orphan", order_by="ChecklistEvidence.created_at"
    )


class OperationalIncident(Base):
    __tablename__ = "operational_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store: Mapped[str] = mapped_column(String(80), default="Grupo Lia", index=True)
    category: Mapped[str] = mapped_column(String(30), index=True)
    severity: Mapped[str] = mapped_column(String(30), index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="aberta", index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    resolved_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    resolved_by: Mapped[User] = relationship(foreign_keys=[resolved_by_user_id])


class ChecklistEvidence(Base):
    __tablename__ = "checklist_evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checklist_run_item_id: Mapped[int] = mapped_column(ForeignKey("checklist_run_items.id"), index=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    storage_provider: Mapped[str] = mapped_column(String(30), default="local")
    file_url: Mapped[str] = mapped_column(String(500), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    checklist_run_item: Mapped[ChecklistRunItem] = relationship(back_populates="evidences")
    uploaded_by: Mapped[User] = relationship()


class AiChatSession(Base):
    __tablename__ = "ai_chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    store: Mapped[str] = mapped_column(String(80), default="Grupo Lia")
    unit: Mapped[str] = mapped_column(String(80), nullable=True)
    title: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    user: Mapped[User] = relationship()
    logs: Mapped[list["AiChatLog"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="AiChatLog.created_at"
    )


class AiChatLog(Base):
    __tablename__ = "ai_chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("ai_chat_sessions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer_summary: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[dict[str, str | int | None]]] = mapped_column(JSON, default=list)
    mode: Mapped[str] = mapped_column(String(30))
    needs_manager_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    session: Mapped[AiChatSession] = relationship(back_populates="logs")
    user: Mapped[User] = relationship()
