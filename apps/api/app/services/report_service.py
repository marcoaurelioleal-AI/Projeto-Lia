from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.report_repository import ReportRepository
from ..schemas import ReportSummaryRead


class ReportService:
    def __init__(self, db: Session) -> None:
        self.repository = ReportRepository(db)

    def summary(self, start_date: date, end_date: date, store: str | None = None) -> ReportSummaryRead:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Intervalo de datas invalido")

        start_at = datetime.combine(start_date, time.min)
        end_at = datetime.combine(end_date, time.max)
        runs = self.repository.list_checklist_runs(start_date=start_date, end_date=end_date, store=store)
        incidents = self.repository.list_incidents(start_at=start_at, end_at=end_at, store=store)

        total_checklists = len(runs)
        total_items = sum(len(run.items) for run in runs)
        completed_items = sum(1 for run in runs for item in run.items if item.done)
        pending_tasks = total_items - completed_items
        completion_percent = round((completed_items / total_items) * 100) if total_items else 0

        return ReportSummaryRead(
            start_date=start_date,
            end_date=end_date,
            store=store,
            total_checklists=total_checklists,
            total_items=total_items,
            completed_items=completed_items,
            completion_percent=completion_percent,
            pending_tasks=pending_tasks,
            total_incidents=len(incidents),
            incidents_by_status=dict(Counter(incident.status for incident in incidents)),
            incidents_by_severity=dict(Counter(incident.severity for incident in incidents)),
            incidents_by_category=dict(Counter(incident.category for incident in incidents)),
            evidences_uploaded=self.repository.count_evidences(start_at=start_at, end_at=end_at, store=store),
        )
