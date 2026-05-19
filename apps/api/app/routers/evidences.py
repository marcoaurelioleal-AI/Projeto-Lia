from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ChecklistEvidenceRead, EvidenceAuditFilterOptionsRead
from ..security import get_current_user, require_permission
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
    user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> list[ChecklistEvidenceRead]:
    return service.list_for_item(item_id, user)


@router.get("/checklists/{run_id}/evidences", response_model=list[ChecklistEvidenceRead])
def list_run_evidences(
    run_id: int,
    user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> list[ChecklistEvidenceRead]:
    return service.list_for_run(run_id, user)


@router.get("/evidences", response_model=list[ChecklistEvidenceRead])
def list_evidences_audit(
    store: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    checklist_title: str | None = None,
    uploaded_by: str | None = None,
    user: User = Depends(require_permission("view_audit")),
    service: EvidenceService = Depends(get_evidence_service),
) -> list[ChecklistEvidenceRead]:
    return service.list_audit(
        user=user,
        store=store,
        start_date=start_date,
        end_date=end_date,
        checklist_title=checklist_title,
        uploaded_by=uploaded_by,
    )


@router.get("/evidences/filter-options", response_model=EvidenceAuditFilterOptionsRead)
def evidence_audit_filter_options(
    user: User = Depends(require_permission("view_audit")),
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceAuditFilterOptionsRead:
    return service.filter_options(user)


@router.get("/evidences/export", response_model=None)
def export_evidences_audit(
    store: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    checklist_title: str | None = None,
    uploaded_by: str | None = None,
    user: User = Depends(require_permission("view_audit")),
    service: EvidenceService = Depends(get_evidence_service),
) -> Response:
    content = service.export_audit_csv(
        user=user,
        store=store,
        start_date=start_date,
        end_date=end_date,
        checklist_title=checklist_title,
        uploaded_by=uploaded_by,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="auditoria-evidencias.csv"'},
    )


@router.get("/evidences/{evidence_id}/file", include_in_schema=False, response_model=None)
def get_evidence_file(
    evidence_id: int,
    user: User = Depends(get_current_user),
    service: EvidenceService = Depends(get_evidence_service),
) -> Response:
    evidence = service.get_file(evidence_id, user)
    if evidence.storage_provider == "supabase":
        return RedirectResponse(service.signed_url_for(evidence), status_code=302)
    return FileResponse(
        path=Path(evidence.file_path),
        media_type=evidence.content_type,
        filename=evidence.original_filename,
    )
