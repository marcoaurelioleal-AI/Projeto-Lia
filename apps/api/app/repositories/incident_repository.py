from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models import OperationalIncident


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_incidents(self, status: str | None = None, store: str | None = None) -> list[OperationalIncident]:
        query = (
            select(OperationalIncident)
            .options(joinedload(OperationalIncident.created_by), joinedload(OperationalIncident.resolved_by))
            .order_by(OperationalIncident.created_at.desc(), OperationalIncident.id.desc())
        )
        if status:
            query = query.where(OperationalIncident.status == status)
        if store:
            query = query.where(OperationalIncident.store == store)
        return list(self.db.scalars(query).all())

    def get_incident(self, incident_id: int) -> OperationalIncident | None:
        return self.db.scalar(
            select(OperationalIncident)
            .options(joinedload(OperationalIncident.created_by), joinedload(OperationalIncident.resolved_by))
            .where(OperationalIncident.id == incident_id)
        )

    def add(self, incident: OperationalIncident) -> OperationalIncident:
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def commit(self) -> None:
        self.db.commit()
