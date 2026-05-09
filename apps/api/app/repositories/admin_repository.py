from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import ChecklistRun, ChecklistTemplate, Manual, ManualSection, OperationalIncident, User


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.name)).all())

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
