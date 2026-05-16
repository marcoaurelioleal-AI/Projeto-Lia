from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import OperationalIncident, User
from ..repositories.incident_repository import IncidentRepository
from ..schemas import OperationalIncidentCreate, OperationalIncidentRead, OperationalIncidentUpdate
from .permission_service import require_store_access, require_user_permission


class IncidentService:
    def __init__(self, db: Session) -> None:
        self.repository = IncidentRepository(db)

    def list_incidents(
        self, user: User, status: str | None = None, store: str | None = None
    ) -> list[OperationalIncidentRead]:
        require_user_permission(user, "manage_incidents")
        store = require_store_access(user, store) if store else require_store_access(user, None)
        incidents = self.repository.list_incidents(status=status, store=store)
        return [self.serialize_incident(incident) for incident in incidents]

    def create_incident(self, payload: OperationalIncidentCreate, user: User) -> OperationalIncidentRead:
        require_user_permission(user, "manage_incidents")
        description = payload.description.strip()
        if not description:
            raise HTTPException(status_code=400, detail="Descricao da ocorrencia e obrigatoria")
        store = require_store_access(user, payload.store.strip() or "Grupo Lia")

        incident = OperationalIncident(
            store=store,
            category=payload.category,
            severity=payload.severity,
            description=description,
            status="aberta",
            created_by_user_id=user.id,
        )
        incident = self.repository.add(incident)
        return self.serialize_incident(self.repository.get_incident(incident.id) or incident)

    def get_incident(self, incident_id: int, user: User) -> OperationalIncidentRead:
        require_user_permission(user, "manage_incidents")
        incident = self.repository.get_incident(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Ocorrencia nao encontrada")
        require_store_access(user, incident.store)
        return self.serialize_incident(incident)

    def update_incident(
        self, incident_id: int, payload: OperationalIncidentUpdate, user: User
    ) -> OperationalIncidentRead:
        require_user_permission(user, "manage_incidents")
        incident = self.repository.get_incident(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Ocorrencia nao encontrada")
        require_store_access(user, incident.store)

        changes = payload.model_dump(exclude_unset=True)
        if "store" in changes and changes["store"] is not None:
            incident.store = require_store_access(user, changes["store"].strip() or "Grupo Lia")
        if "category" in changes and changes["category"] is not None:
            incident.category = changes["category"]
        if "severity" in changes and changes["severity"] is not None:
            incident.severity = changes["severity"]
        if "description" in changes and changes["description"] is not None:
            description = changes["description"].strip()
            if not description:
                raise HTTPException(status_code=400, detail="Descricao da ocorrencia e obrigatoria")
            incident.description = description
        if "status" in changes and changes["status"] is not None:
            incident.status = changes["status"]
            if incident.status == "resolvida" and incident.resolved_at is None:
                incident.resolved_at = datetime.now(UTC).replace(tzinfo=None)
                incident.resolved_by_user_id = user.id

        self.repository.commit()
        refreshed = self.repository.get_incident(incident_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Ocorrencia nao encontrada")
        return self.serialize_incident(refreshed)

    @staticmethod
    def serialize_incident(incident: OperationalIncident) -> OperationalIncidentRead:
        return OperationalIncidentRead(
            id=incident.id,
            store=incident.store,
            category=incident.category,
            severity=incident.severity,
            description=incident.description,
            status=incident.status,
            created_by=incident.created_by.name if incident.created_by else None,
            created_at=incident.created_at,
            resolved_at=incident.resolved_at,
            resolved_by=incident.resolved_by.name if incident.resolved_by else None,
        )
