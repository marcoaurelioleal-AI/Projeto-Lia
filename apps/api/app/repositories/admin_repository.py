from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import ChecklistRun, ChecklistTemplate, Manual, ManualSection, OperationalIncident, Store, User


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.active.desc(), User.name)).all())

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_user_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def add_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_stores(self) -> list[Store]:
        return list(self.db.scalars(select(Store).order_by(Store.active.desc(), Store.name)).all())

    def get_store(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_store_by_name(self, name: str) -> Store | None:
        return self.db.scalar(select(Store).where(Store.name == name))

    def add_store(self, store: Store) -> Store:
        self.db.add(store)
        self.db.commit()
        self.db.refresh(store)
        return store

    def list_manuals(self) -> list[Manual]:
        return list(
            self.db.scalars(
                select(Manual)
                .options(selectinload(Manual.sections).selectinload(ManualSection.steps))
                .order_by(Manual.unit)
            ).all()
        )

    def list_checklist_templates(self) -> list[ChecklistTemplate]:
        return list(
            self.db.scalars(
                select(ChecklistTemplate).options(selectinload(ChecklistTemplate.items)).order_by(ChecklistTemplate.title)
            ).all()
        )

    def list_store_names(self) -> list[str]:
        names: set[str] = set()
        for statement in (
            select(Manual.unit).distinct(),
            select(ChecklistTemplate.store).distinct(),
            select(ChecklistRun.store).distinct(),
            select(OperationalIncident.store).distinct(),
        ):
            names.update(name for name in self.db.scalars(statement).all() if name)
        if not names:
            names.update({"Grupo Lia", "Lia Burguer", "Lia Pizza", "Lia Salgados"})
        return sorted(names)

    def commit(self) -> None:
        self.db.commit()
