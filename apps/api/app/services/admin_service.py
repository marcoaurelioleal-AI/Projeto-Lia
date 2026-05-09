from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import ChecklistTemplate, Manual, User
from ..repositories.admin_repository import AdminRepository
from ..schemas import StoreRead


class AdminService:
    def __init__(self, db: Session) -> None:
        self.repository = AdminRepository(db)

    def list_users(self) -> list[User]:
        return self.repository.list_users()

    def list_stores(self) -> list[StoreRead]:
        return [StoreRead(name=name) for name in self.repository.list_store_names()]

    def list_checklist_templates(self) -> list[ChecklistTemplate]:
        return self.repository.list_checklist_templates()

    def list_manuals(self) -> list[Manual]:
        return self.repository.list_manuals()
