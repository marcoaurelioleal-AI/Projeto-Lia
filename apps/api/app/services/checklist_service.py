from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ChecklistRun, User
from ..repositories.checklist_repository import ChecklistRepository
from ..schemas import ChecklistItemRead, ChecklistItemUpdate, ChecklistRunRead
from ..seed import ensure_runs_for_date
from .permission_service import require_store_access, require_user_permission


class ChecklistService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ChecklistRepository(db)

    def list_checklists(self, run_date: date | None, store: str, user: User) -> list[ChecklistRunRead]:
        require_user_permission(user, "manage_checklists")
        store = require_store_access(user, store) or "Grupo Lia"
        target_date = run_date or date.today()
        ensure_runs_for_date(self.db, target_date, store)
        runs = self.repository.list_runs_for_date(target_date, store)
        return [self.serialize_run(run) for run in runs]

    def update_item(self, run_id: int, payload: ChecklistItemUpdate, user: User) -> ChecklistRunRead:
        require_user_permission(user, "manage_checklists")
        item = self.repository.get_run_item(run_id, payload.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item de checklist nao encontrado")
        require_store_access(user, item.run.store if item.run else None)

        item.done = payload.done
        item.completed_at = datetime.now(UTC).replace(tzinfo=None) if payload.done else None
        item.completed_by_user_id = user.id if payload.done else None
        self.repository.commit()

        run = self.repository.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Checklist nao encontrado")
        return self.serialize_run(run)

    def update_closing_note(self, run_id: int, closing_note: str, user: User) -> ChecklistRunRead:
        require_user_permission(user, "manage_checklists")
        run = self.repository.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Checklist nao encontrado")
        require_store_access(user, run.store)

        run.closing_note = closing_note
        self.repository.commit()

        refreshed_run = self.repository.get_run(run_id)
        if not refreshed_run:
            raise HTTPException(status_code=404, detail="Checklist nao encontrado")
        return self.serialize_run(refreshed_run)

    @staticmethod
    def serialize_run(run: ChecklistRun) -> ChecklistRunRead:
        total = len(run.items)
        completed = sum(1 for item in run.items if item.done)
        progress = round((completed / total) * 100) if total else 0
        return ChecklistRunRead(
            id=run.id,
            title=run.template.title,
            category=run.template.category,
            store=run.store,
            run_date=run.run_date,
            progress=progress,
            completed=completed,
            total=total,
            closing_note=run.closing_note,
            items=[
                ChecklistItemRead(
                    id=item.id,
                    section=item.template_item.section,
                    text=item.template_item.text,
                    done=item.done,
                    completed_at=item.completed_at,
                    completed_by=item.completed_by.name if item.completed_by else None,
                )
                for item in run.items
            ],
        )
