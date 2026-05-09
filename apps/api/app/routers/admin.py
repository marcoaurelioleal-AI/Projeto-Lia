from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChecklistTemplate, Manual, User
from ..schemas import ChecklistTemplateRead, ManualRead, StoreRead, UserRead
from ..security import require_admin_user
from ..services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


@router.get("/users", response_model=list[UserRead])
def list_users(
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> list[User]:
    return service.list_users()


@router.get("/stores", response_model=list[StoreRead])
def list_stores(
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> list[StoreRead]:
    return service.list_stores()


@router.get("/checklist-templates", response_model=list[ChecklistTemplateRead])
def list_checklist_templates(
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> list[ChecklistTemplate]:
    return service.list_checklist_templates()


@router.get("/manuals", response_model=list[ManualRead])
def list_manuals(
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> list[Manual]:
    return service.list_manuals()
