from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChecklistTemplate, Manual, Store, User
from ..schemas import (
    ChecklistTemplateRead,
    ManualRead,
    StoreCreate,
    StoreRead,
    StoreUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)
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


@router.post("/users", response_model=UserRead)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> User:
    return service.create_user(payload)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> User:
    return service.update_user(user_id, payload, current_user)


@router.delete("/users/{user_id}", response_model=UserRead)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> User:
    return service.deactivate_user(user_id, current_user)


@router.get("/stores", response_model=list[StoreRead])
def list_stores(
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> list[Store]:
    return service.list_stores()


@router.post("/stores", response_model=StoreRead)
def create_store(
    payload: StoreCreate,
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> Store:
    return service.create_store(payload)


@router.patch("/stores/{store_id}", response_model=StoreRead)
def update_store(
    store_id: int,
    payload: StoreUpdate,
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> Store:
    return service.update_store(store_id, payload)


@router.delete("/stores/{store_id}", response_model=StoreRead)
def deactivate_store(
    store_id: int,
    _: User = Depends(require_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> Store:
    return service.deactivate_store(store_id)


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
