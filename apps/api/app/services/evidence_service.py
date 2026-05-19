from __future__ import annotations

import csv
import io
from datetime import date, datetime, time
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..models import ChecklistEvidence, ChecklistRunItem, User
from ..repositories.evidence_repository import EvidenceRepository
from ..schemas import ChecklistEvidenceRead, EvidenceAuditFilterOptionsRead
from .audit_service import AuditService
from .permission_service import require_store_access, require_user_permission
from .storage_service import SupabaseStorageService, get_storage_service


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.repository = EvidenceRepository(db)
        self.storage = get_storage_service()

    async def upload_checklist_evidence(
        self, item_id: int, file: UploadFile, user: User
    ) -> ChecklistEvidenceRead:
        require_user_permission(user, "upload_evidences")
        item = self.repository.get_run_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item de checklist nao encontrado")
        self._require_item_store_access(user, item)

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

    def list_for_item(self, item_id: int, user: User) -> list[ChecklistEvidenceRead]:
        require_user_permission(user, "view_evidences")
        item = self.repository.get_run_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item de checklist nao encontrado")
        self._require_item_store_access(user, item)
        return [self.serialize_evidence(evidence) for evidence in self.repository.list_for_item(item_id)]

    def list_for_run(self, run_id: int, user: User) -> list[ChecklistEvidenceRead]:
        require_user_permission(user, "view_evidences")
        run = self.repository.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Checklist nao encontrado")
        require_store_access(user, run.store)
        return [self.serialize_evidence(evidence) for evidence in self.repository.list_for_run(run_id)]

    def list_audit(
        self,
        user: User,
        store: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        checklist_title: str | None = None,
        uploaded_by: str | None = None,
    ) -> list[ChecklistEvidenceRead]:
        require_user_permission(user, "view_audit")
        store = require_store_access(user, store) if store else require_store_access(user, None)
        start_at = datetime.combine(start_date, time.min) if start_date else None
        end_at = datetime.combine(end_date, time.max) if end_date else None
        rows = [
            self.serialize_evidence(evidence)
            for evidence in self.repository.list_audit(
                store=store,
                start_at=start_at,
                end_at=end_at,
                checklist_title=checklist_title,
                uploaded_by=uploaded_by,
            )
        ]
        self._record_audit_action(
            user=user,
            action="evidence_audit_list",
            store=store,
            details={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "checklist_title": checklist_title,
                "uploaded_by": uploaded_by,
                "result_count": len(rows),
            },
        )
        return rows

    def filter_options(self, user: User) -> EvidenceAuditFilterOptionsRead:
        require_user_permission(user, "view_audit")
        store = require_store_access(user, None)
        options = self.repository.list_filter_options(store=store)
        return EvidenceAuditFilterOptionsRead(**options)

    def export_audit_csv(
        self,
        user: User,
        store: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        checklist_title: str | None = None,
        uploaded_by: str | None = None,
    ) -> str:
        rows = self.list_audit(
            user=user,
            store=store,
            start_date=start_date,
            end_date=end_date,
            checklist_title=checklist_title,
            uploaded_by=uploaded_by,
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "loja",
                "checklist",
                "item",
                "usuario",
                "arquivo",
                "tipo",
                "tamanho_bytes",
                "criado_em",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.store or "",
                    row.checklist_title or "",
                    row.item_text or "",
                    row.uploaded_by or "",
                    row.original_filename,
                    row.content_type,
                    row.file_size,
                    row.created_at.isoformat(),
                ]
            )
        self._record_audit_action(
            user=user,
            action="evidence_audit_export",
            store=store,
            details={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "checklist_title": checklist_title,
                "uploaded_by": uploaded_by,
                "result_count": len(rows),
            },
        )
        return output.getvalue()

    def get_file(self, evidence_id: int, user: User) -> ChecklistEvidence:
        require_user_permission(user, "view_evidences")
        evidence = self.repository.get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidencia nao encontrada")
        self._require_evidence_store_access(user, evidence)
        if evidence.storage_provider == "local" and not Path(evidence.file_path).exists():
            raise HTTPException(status_code=404, detail="Arquivo da evidencia nao encontrado")
        item = evidence.checklist_run_item
        run = item.run if item else None
        self._record_audit_action(
            user=user,
            action="evidence_file_view",
            store=run.store if run else None,
            entity_id=str(evidence.id),
            details={"filename": evidence.original_filename},
        )
        return evidence

    def signed_url_for(self, evidence: ChecklistEvidence) -> str:
        if not isinstance(self.storage, SupabaseStorageService):
            raise HTTPException(status_code=400, detail="Storage atual nao suporta URL assinada")
        return self.storage.create_signed_url(evidence.file_path)

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

    @staticmethod
    def _require_item_store_access(user: User, item: ChecklistRunItem) -> None:
        require_store_access(user, item.run.store if item.run else None)

    @staticmethod
    def _require_evidence_store_access(user: User, evidence: ChecklistEvidence) -> None:
        item = evidence.checklist_run_item
        run = item.run if item else None
        require_store_access(user, run.store if run else None)

    def _record_audit_action(
        self,
        *,
        user: User,
        action: str,
        store: str | None,
        details: dict[str, object],
        entity_id: str | None = None,
    ) -> None:
        AuditService(self.repository.db).record(
            action=action,
            actor_user_id=user.id,
            actor_username=user.username,
            actor_role=user.role,
            entity_type="evidences",
            entity_id=entity_id,
            store=store,
            details=details,
        )
