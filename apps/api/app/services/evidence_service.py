from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..models import ChecklistEvidence, User
from ..repositories.evidence_repository import EvidenceRepository
from ..schemas import ChecklistEvidenceRead
from .storage_service import LocalStorageService


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.repository = EvidenceRepository(db)
        self.storage = LocalStorageService()

    async def upload_checklist_evidence(
        self, item_id: int, file: UploadFile, user: User
    ) -> ChecklistEvidenceRead:
        item = self.repository.get_run_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item de checklist nao encontrado")

        storage_result = await self.storage.save_file(file)
        evidence = ChecklistEvidence(
            checklist_run_item_id=item.id,
            uploaded_by_user_id=user.id,
            storage_provider=storage_result.storage_provider,
            file_path=storage_result.file_path,
            original_filename=storage_result.original_filename,
            content_type=storage_result.content_type,
            file_size=storage_result.file_size,
        )
        evidence = self.repository.add(evidence)
        evidence.file_url = f"/evidences/{evidence.id}/file"
        evidence = self.repository.commit_refresh(evidence)
        refreshed = self.repository.get_evidence(evidence.id) or evidence
        return self.serialize_evidence(refreshed)

    def list_for_item(self, item_id: int) -> list[ChecklistEvidenceRead]:
        return [self.serialize_evidence(evidence) for evidence in self.repository.list_for_item(item_id)]

    def list_for_run(self, run_id: int) -> list[ChecklistEvidenceRead]:
        return [self.serialize_evidence(evidence) for evidence in self.repository.list_for_run(run_id)]

    def list_audit(
        self,
        store: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ChecklistEvidenceRead]:
        start_at = datetime.combine(start_date, time.min) if start_date else None
        end_at = datetime.combine(end_date, time.max) if end_date else None
        return [
            self.serialize_evidence(evidence)
            for evidence in self.repository.list_audit(store=store, start_at=start_at, end_at=end_at)
        ]

    def get_file(self, evidence_id: int) -> ChecklistEvidence:
        evidence = self.repository.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidencia nao encontrada")
        if not Path(evidence.file_path).exists():
            raise HTTPException(status_code=404, detail="Arquivo da evidencia nao encontrado")
        return evidence

    @staticmethod
    def serialize_evidence(evidence: ChecklistEvidence) -> ChecklistEvidenceRead:
        item = evidence.checklist_run_item
        run = item.run if item else None
        template_item = item.template_item if item else None
        return ChecklistEvidenceRead(
            id=evidence.id,
            checklist_run_item_id=evidence.checklist_run_item_id,
            uploaded_by=evidence.uploaded_by.name if evidence.uploaded_by else None,
            storage_provider=evidence.storage_provider,
            file_url=evidence.file_url,
            original_filename=evidence.original_filename,
            content_type=evidence.content_type,
            file_size=evidence.file_size,
            created_at=evidence.created_at,
            run_id=run.id if run else None,
            store=run.store if run else None,
            checklist_title=run.template.title if run and run.template else None,
            item_text=template_item.text if template_item else None,
        )
