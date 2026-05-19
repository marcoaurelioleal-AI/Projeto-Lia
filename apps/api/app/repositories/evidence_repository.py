from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..models import ChecklistEvidence, ChecklistRun, ChecklistRunItem, ChecklistTemplate, User


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

    def get_run(self, run_id: int) -> ChecklistRun | None:
        return self.db.scalar(
            select(ChecklistRun)
            .options(joinedload(ChecklistRun.template), joinedload(ChecklistRun.items))
            .where(ChecklistRun.id == run_id)
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
        checklist_title: str | None = None,
        uploaded_by: str | None = None,
        limit: int | None = None,
    ) -> list[ChecklistEvidence]:
        query = select(ChecklistEvidence).join(ChecklistRunItem).join(ChecklistRun)
        if store:
            query = query.where(ChecklistRun.store == store)
        if start_at:
            query = query.where(ChecklistEvidence.created_at >= start_at)
        if end_at:
            query = query.where(ChecklistEvidence.created_at <= end_at)
        if checklist_title:
            query = query.join(ChecklistTemplate, ChecklistRun.template_id == ChecklistTemplate.id).where(
                func.lower(ChecklistTemplate.title).like(f"%{checklist_title.strip().lower()}%")
            )
        if uploaded_by:
            user_filter = f"%{uploaded_by.strip().lower()}%"
            query = query.join(User, ChecklistEvidence.uploaded_by_user_id == User.id).where(
                or_(func.lower(User.name).like(user_filter), func.lower(User.username).like(user_filter))
            )
        query = query.order_by(ChecklistEvidence.created_at.desc(), ChecklistEvidence.id.desc())
        if limit:
            query = query.limit(limit)
        return self._with_context(query)

    def list_filter_options(self, store: str | None = None) -> dict[str, list[str]]:
        base_filters = []
        if store:
            base_filters.append(ChecklistRun.store == store)

        stores_query = select(ChecklistRun.store).join(ChecklistRunItem).join(ChecklistEvidence).distinct()
        checklists_query = (
            select(ChecklistTemplate.title)
            .join(ChecklistRun, ChecklistRun.template_id == ChecklistTemplate.id)
            .join(ChecklistRunItem)
            .join(ChecklistEvidence)
            .distinct()
        )
        users_query = (
            select(User.name)
            .join(ChecklistEvidence, ChecklistEvidence.uploaded_by_user_id == User.id)
            .join(ChecklistRunItem)
            .join(ChecklistRun)
            .distinct()
        )

        if base_filters:
            stores_query = stores_query.where(*base_filters)
            checklists_query = checklists_query.where(*base_filters)
            users_query = users_query.where(*base_filters)

        return {
            "stores": sorted(name for name in self.db.scalars(stores_query).all() if name),
            "checklists": sorted(title for title in self.db.scalars(checklists_query).all() if title),
            "users": sorted(name for name in self.db.scalars(users_query).all() if name),
        }

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
