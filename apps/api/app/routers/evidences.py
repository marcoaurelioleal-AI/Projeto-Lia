from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ChecklistEvidenceRead
from ..security import get_current_user, require_admin_user
from ..services.evidence_service import EvidenceService

router = APIRouter(tags=["evidences"])


def get_evidence_service(db: Session = Depends(get_db)) -> EvidenceService:
    return EvidenceService(db)


@router.post("/checklists/items/{item_id}/evidences", response_model=ChecklistEvidenceRead)
async def upload_checklist_evidence(
    item_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> ChecklistEvidenceRead:
    return await service.upload_checklist_evidence(item_id, file, user)


@router.get("/checklists/items/{item_id}/evidences", response_model=list[ChecklistEvidenceRead])
def list_item_evidences(
    item_id: int,
    _: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> list[ChecklistEvidenceRead]:
    return service.list_for_item(item_id)


@router.get("/checklists/{run_id}/evidences", response_model=list[ChecklistEvidenceRead])
def list_run_evidences(
    run_id: int,
    _: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> list[ChecklistEvidenceRead]:
    return service.list_for_run(run_id)


@router.get("/evidences", response_model=list[ChecklistEvidenceRead])
def list_evidences_audit(
    store: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    _: User = Depends(require_admin_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> list[ChecklistEvidenceRead]:
    return service.list_audit(store=store, start_date=start_date, end_date=end_date)


@router.get("/evidences/{evidence_id}/file", include_in_schema=False)
def get_evidence_file(
    evidence_id: int,
    _: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> FileResponse:
    evidence = service.get_file(evidence_id)
    return FileResponse(
        path=Path(evidence.file_path),
        media_type=evidence.content_type,
        filename=evidence.original_filename,
    )
