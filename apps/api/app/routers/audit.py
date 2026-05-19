from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, User
from ..schemas import AuditLogRead
from ..security import require_permission
from ..services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


@router.get("/logs", response_model=list[AuditLogRead])
def list_audit_logs(
    action: str | None = None,
    status: str | None = None,
    entity_type: str | None = None,
    store: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(require_permission("view_audit")),
    service: AuditService = Depends(get_audit_service),
) -> list[AuditLog]:
    return service.list_logs(
        user=user,
        action=action,
        status=status,
        entity_type=entity_type,
        store=store,
        limit=limit,
    )
