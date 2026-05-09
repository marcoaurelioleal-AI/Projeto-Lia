from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import ChecklistEvidence, ChecklistRun, ChecklistRunItem, OperationalIncident


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_checklist_runs(self, start_date: date, end_date: date, store: str | None = None) -> list[ChecklistRun]:
        query = (
            select(ChecklistRun)
            .options(selectinload(ChecklistRun.items))
            .where(ChecklistRun.run_date >= start_date, ChecklistRun.run_date <= end_date)
        )
        if store:
            query = query.where(ChecklistRun.store == store)
        return list(self.db.scalars(query).all())

    def list_incidents(
        self,
        start_at: datetime,
        end_at: datetime,
        store: str | None = None,
    ) -> list[OperationalIncident]:
        query = select(OperationalIncident).where(
            OperationalIncident.created_at >= start_at,
            OperationalIncident.created_at <= end_at,
        )
        if store:
            query = query.where(OperationalIncident.store == store)
        return list(self.db.scalars(query).all())

    def count_evidences(
        self,
        start_at: datetime,
        end_at: datetime,
        store: str | None = None,
    ) -> int:
        query = select(func.count(ChecklistEvidence.id)).where(
            ChecklistEvidence.created_at >= start_at,
            ChecklistEvidence.created_at <= end_at,
        )
        if store:
            query = query.join(ChecklistRunItem).join(ChecklistRun).where(ChecklistRun.store == store)
        return int(self.db.scalar(query) or 0)
