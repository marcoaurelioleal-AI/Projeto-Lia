from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ChecklistItemUpdate, ChecklistRunRead, ClosingNoteUpdate
from ..security import get_current_user
from ..services.checklist_service import ChecklistService

router = APIRouter(prefix="/checklists", tags=["checklists"])


def get_checklist_service(db: Session = Depends(get_db)) -> ChecklistService:
    return ChecklistService(db)


@router.get("", response_model=list[ChecklistRunRead])
def list_checklists(
    run_date: date | None = None,
    store: str = "Grupo Lia",
    user: User = Depends(get_current_user),
    service: ChecklistService = Depends(get_checklist_service),
) -> list[ChecklistRunRead]:
    return service.list_checklists(run_date, store, user)


@router.patch("/{run_id}/items", response_model=ChecklistRunRead)
def update_checklist_item(
    run_id: int,
    payload: ChecklistItemUpdate,
    user: User = Depends(get_current_user),
    service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistRunRead:
    return service.update_item(run_id, payload, user)


@router.patch("/{run_id}/closing-note", response_model=ChecklistRunRead)
def update_closing_note(
    run_id: int,
    payload: ClosingNoteUpdate,
    user: User = Depends(get_current_user),
    service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistRunRead:
    return service.update_closing_note(run_id, payload.closing_note, user)
