from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    ChecklistRun,
    ChecklistTemplate,
    ChecklistTemplateItem,
    Manual,
    ManualSection,
    ManualStep,
    OperationalIncident,
    Store,
    User,
)


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(self) -> list[User]:
        return list(
            self.db.scalars(
                select(User).options(selectinload(User.store)).order_by(User.active.desc(), User.name)
            ).all()
        )

    def get_user(self, user_id: int) -> User | None:
        return self.db.scalar(select(User).options(selectinload(User.store)).where(User.id == user_id))

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

    def get_manual(self, manual_id: int) -> Manual | None:
        return self.db.scalar(
            select(Manual)
            .options(selectinload(Manual.sections).selectinload(ManualSection.steps))
            .where(Manual.id == manual_id)
        )

    def get_manual_by_unit(self, unit: str) -> Manual | None:
        return self.db.scalar(select(Manual).where(Manual.unit == unit))

    def add_manual(self, manual: Manual) -> Manual:
        self.db.add(manual)
        self.db.commit()
        self.db.refresh(manual)
        return manual

    def get_manual_section(self, section_id: int) -> ManualSection | None:
        return self.db.get(ManualSection, section_id)

    def get_manual_step(self, step_id: int) -> ManualStep | None:
        return self.db.get(ManualStep, step_id)

    def next_manual_section_position(self, manual_id: int) -> int:
        manual = self.get_manual(manual_id)
        if not manual or not manual.sections:
            return 0
        return max(section.position for section in manual.sections) + 1

    def next_manual_step_position(self, section_id: int) -> int:
        section = self.get_manual_section(section_id)
        if not section or not section.steps:
            return 0
        return max(step.position for step in section.steps) + 1

    def list_checklist_templates(self) -> list[ChecklistTemplate]:
        return list(
            self.db.scalars(
                select(ChecklistTemplate).options(selectinload(ChecklistTemplate.items)).order_by(ChecklistTemplate.title)
            ).all()
        )

    def get_checklist_template(self, template_id: int) -> ChecklistTemplate | None:
        return self.db.scalar(
            select(ChecklistTemplate).options(selectinload(ChecklistTemplate.items)).where(ChecklistTemplate.id == template_id)
        )

    def get_checklist_template_by_title(self, title: str) -> ChecklistTemplate | None:
        return self.db.scalar(select(ChecklistTemplate).where(ChecklistTemplate.title == title))

    def add_checklist_template(self, template: ChecklistTemplate) -> ChecklistTemplate:
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_checklist_template_item(self, item_id: int) -> ChecklistTemplateItem | None:
        return self.db.get(ChecklistTemplateItem, item_id)

    def next_template_item_position(self, template_id: int) -> int:
        template = self.get_checklist_template(template_id)
        if not template or not template.items:
            return 0
        return max(item.position for item in template.items) + 1

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
