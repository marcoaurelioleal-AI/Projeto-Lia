from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ChecklistTemplate, Manual, Store, User
from ..repositories.admin_repository import AdminRepository
from ..schemas import StoreCreate, StoreUpdate, UserCreate, UserUpdate
from ..security import hash_password


class AdminService:
    def __init__(self, db: Session) -> None:
        self.repository = AdminRepository(db)

    def list_users(self) -> list[User]:
        return self.repository.list_users()

    def create_user(self, payload: UserCreate) -> User:
        username = payload.username.strip().lower()
        if self.repository.get_user_by_username(username):
            raise HTTPException(status_code=409, detail="Usuario ja cadastrado")

        return self.repository.add_user(
            User(
                username=username,
                name=payload.name.strip(),
                role=payload.role,
                password_hash=hash_password(payload.password),
                active=True,
            )
        )

    def update_user(self, user_id: int, payload: UserUpdate, current_user: User) -> User:
        user = self.repository.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario nao encontrado")

        changes = payload.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] is not None:
            user.name = changes["name"].strip()
        if "role" in changes and changes["role"] is not None:
            user.role = changes["role"]
        if "active" in changes and changes["active"] is not None:
            if user.id == current_user.id and changes["active"] is False:
                raise HTTPException(status_code=400, detail="Nao e possivel desativar o proprio usuario")
            user.active = changes["active"]

        self.repository.commit()
        return user

    def deactivate_user(self, user_id: int, current_user: User) -> User:
        return self.update_user(user_id, UserUpdate(active=False), current_user)

    def list_stores(self) -> list[Store]:
        return self.repository.list_stores()

    def create_store(self, payload: StoreCreate) -> Store:
        name = payload.name.strip()
        if self.repository.get_store_by_name(name):
            raise HTTPException(status_code=409, detail="Loja ja cadastrada")
        return self.repository.add_store(Store(name=name, active=True))

    def update_store(self, store_id: int, payload: StoreUpdate) -> Store:
        store = self.repository.get_store(store_id)
        if not store:
            raise HTTPException(status_code=404, detail="Loja nao encontrada")

        changes = payload.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] is not None:
            name = changes["name"].strip()
            existing = self.repository.get_store_by_name(name)
            if existing and existing.id != store.id:
                raise HTTPException(status_code=409, detail="Loja ja cadastrada")
            store.name = name
        if "active" in changes and changes["active"] is not None:
            store.active = changes["active"]

        self.repository.commit()
        return store

    def deactivate_store(self, store_id: int) -> Store:
        return self.update_store(store_id, StoreUpdate(active=False))

    def list_checklist_templates(self) -> list[ChecklistTemplate]:
        return self.repository.list_checklist_templates()

    def list_manuals(self) -> list[Manual]:
        return self.repository.list_manuals()
