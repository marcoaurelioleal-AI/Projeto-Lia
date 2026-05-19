from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories.evidence_repository import EvidenceRepository
from ..repositories.report_repository import ReportRepository
from ..schemas import ExecutiveDashboardRead, ReportSummaryRead, StorePendingSummaryRead
from ..models import User
from ..seed import ensure_runs_for_date
from .evidence_service import EvidenceService
from .incident_service import IncidentService
from .permission_service import require_store_access, require_user_permission


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ReportRepository(db)
        self.evidence_repository = EvidenceRepository(db)

    def summary(self, start_date: date, end_date: date, user: User, store: str | None = None) -> ReportSummaryRead:
        require_user_permission(user, "view_reports")
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Intervalo de datas invalido")
        store = require_store_access(user, store) if store else require_store_access(user, None)

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

    def executive_dashboard(self, user: User) -> ExecutiveDashboardRead:
        require_user_permission(user, "view_reports")
        today = date.today()
        visible_stores = self._visible_stores(user)
        store_scope = require_store_access(user, None)

        store_rankings = [self._store_pending_summary(store, today) for store in visible_stores]
        store_rankings.sort(key=lambda item: (item.pending_tasks, item.total_items), reverse=True)

        critical_incidents = [
            IncidentService.serialize_incident(incident)
            for incident in self.repository.list_open_critical_incidents(store=store_scope, limit=6)
        ]
        recent_evidences = [
            EvidenceService.serialize_evidence(evidence)
            for evidence in self.evidence_repository.list_audit(store=store_scope, limit=6)
        ]

        return ExecutiveDashboardRead(
            today=today,
            visible_stores=visible_stores,
            summary_7d=self.summary(start_date=today - timedelta(days=6), end_date=today, user=user),
            summary_30d=self.summary(start_date=today - timedelta(days=29), end_date=today, user=user),
            store_rankings=store_rankings,
            critical_incidents=critical_incidents,
            recent_evidences=recent_evidences,
        )

    def _visible_stores(self, user: User) -> list[str]:
        scoped_store = require_store_access(user, None)
        if scoped_store:
            return [scoped_store]
        stores = self.repository.list_active_store_names()
        return stores or ["Grupo Lia", "Lia Burguer", "Lia Pizza", "Lia Salgados"]

    def _store_pending_summary(self, store: str, target_date: date) -> StorePendingSummaryRead:
        ensure_runs_for_date(self.db, target_date, store)
        runs = self.repository.list_checklist_runs(start_date=target_date, end_date=target_date, store=store)
        total_items = sum(len(run.items) for run in runs)
        completed_items = sum(1 for run in runs for item in run.items if item.done)
        pending_tasks = total_items - completed_items
        completion_percent = round((completed_items / total_items) * 100) if total_items else 0
        return StorePendingSummaryRead(
            store=store,
            total_checklists=len(runs),
            total_items=total_items,
            completed_items=completed_items,
            pending_tasks=pending_tasks,
            completion_percent=completion_percent,
        )
