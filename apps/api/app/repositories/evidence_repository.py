from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models import ChecklistEvidence, ChecklistRun, ChecklistRunItem


class EvidenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_run_item(self, item_id: int) -> ChecklistRunItem | None:
        return self.db.scalar(
            select(ChecklistRunItem)
            .options(
                joinedload(ChecklistRunItem.run).joinedload(ChecklistRun.template),
                joinedload(ChecklistRunItem.template_item),
            )
            .where(ChecklistRunItem.id == item_id)
        )

    def add(self, evidence: ChecklistEvidence) -> ChecklistEvidence:
        self.db.add(evidence)
        self.db.flush()
        return evidence

    def commit_refresh(self, evidence: ChecklistEvidence) -> ChecklistEvidence:
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def get_evidence(self, evidence_id: int) -> ChecklistEvidence | None:
        return self.db.scalar(
            select(ChecklistEvidence)
            .options(
                joinedload(ChecklistEvidence.uploaded_by),
                joinedload(ChecklistEvidence.checklist_run_item)
                .joinedload(ChecklistRunItem.run)
                .joinedload(ChecklistRun.template),
                joinedload(ChecklistEvidence.checklist_run_item).joinedload(ChecklistRunItem.template_item),
            )
            .where(ChecklistEvidence.id == evidence_id)
        )

    def list_for_item(self, item_id: int) -> list[ChecklistEvidence]:
        return self._with_context(
            select(ChecklistEvidence)
            .where(ChecklistEvidence.checklist_run_item_id == item_id)
            .order_by(ChecklistEvidence.created_at.desc(), ChecklistEvidence.id.desc())
        )

    def list_for_run(self, run_id: int) -> list[ChecklistEvidence]:
        return self._with_context(
            select(ChecklistEvidence)
            .join(ChecklistRunItem)
            .where(ChecklistRunItem.run_id == run_id)
            .order_by(ChecklistEvidence.created_at.desc(), ChecklistEvidence.id.desc())
        )

    def list_audit(
        self,
        store: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[ChecklistEvidence]:
        query = select(ChecklistEvidence).join(ChecklistRunItem).join(ChecklistRun)
        if store:
            query = query.where(ChecklistRun.store == store)
        if start_at:
            query = query.where(ChecklistEvidence.created_at >= start_at)
        if end_at:
            query = query.where(ChecklistEvidence.created_at <= end_at)
        return self._with_context(query.order_by(ChecklistEvidence.created_at.desc(), ChecklistEvidence.id.desc()))

    def _with_context(self, query) -> list[ChecklistEvidence]:
        return list(
            self.db.scalars(
                query.options(
                    joinedload(ChecklistEvidence.uploaded_by),
                    joinedload(ChecklistEvidence.checklist_run_item)
                    .joinedload(ChecklistRunItem.run)
                    .joinedload(ChecklistRun.template),
                    joinedload(ChecklistEvidence.checklist_run_item).joinedload(ChecklistRunItem.template_item),
                )
            ).all()
        )
