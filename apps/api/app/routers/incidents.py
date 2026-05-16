from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import IncidentStatus, OperationalIncidentCreate, OperationalIncidentRead, OperationalIncidentUpdate
from ..security import get_current_user
from ..services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_incident_service(db: Session = Depends(get_db)) -> IncidentService:
    return IncidentService(db)


@router.get("", response_model=list[OperationalIncidentRead])
def list_incidents(
    status: IncidentStatus | None = None,
    store: str | None = None,
    user: User = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> list[OperationalIncidentRead]:
    return service.list_incidents(user=user, status=status, store=store)


@router.post("", response_model=OperationalIncidentRead)
def create_incident(
    payload: OperationalIncidentCreate,
    user: User = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> OperationalIncidentRead:
    return service.create_incident(payload, user)


@router.get("/{incident_id}", response_model=OperationalIncidentRead)
def get_incident(
    incident_id: int,
    user: User = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> OperationalIncidentRead:
    return service.get_incident(incident_id, user)


@router.patch("/{incident_id}", response_model=OperationalIncidentRead)
def update_incident(
    incident_id: int,
    payload: OperationalIncidentUpdate,
    user: User = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> OperationalIncidentRead:
    return service.update_incident(incident_id, payload, user)
