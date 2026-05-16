from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import ChecklistTemplate, ChecklistTemplateItem, Manual, ManualSection, ManualStep, Store, User
from ..repositories.admin_repository import AdminRepository
from ..schemas import (
    ChecklistTemplateCreate,
    ChecklistTemplateItemCreate,
    ChecklistTemplateItemUpdate,
    ChecklistTemplateUpdate,
    ManualCreate,
    ManualSectionCreate,
    ManualSectionUpdate,
    ManualStepCreate,
    ManualStepUpdate,
    ManualUpdate,
    StoreCreate,
    StoreUpdate,
    UserCreate,
    UserUpdate,
)
from ..security import hash_password
from .permission_service import validate_user_store_assignment


class AdminService:
    def __init__(self, db: Session) -> None:
        self.repository = AdminRepository(db)

    def list_users(self) -> list[User]:
        return self.repository.list_users()

    def create_user(self, payload: UserCreate) -> User:
        username = payload.username.strip().lower()
        if self.repository.get_user_by_username(username):
            raise HTTPException(status_code=409, detail="Usuario ja cadastrado")
        store = self.repository.get_store(payload.store_id) if payload.store_id else None
        if payload.store_id and not store:
            raise HTTPException(status_code=404, detail="Loja nao encontrada")
        validate_user_store_assignment(payload.role, store)

        return self.repository.add_user(
            User(
                username=username,
                name=payload.name.strip(),
                role=payload.role,
                store_id=store.id if store else None,
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
        if "store_id" in changes:
            if changes["store_id"] is None:
                user.store_id = None
            else:
                store = self.repository.get_store(changes["store_id"])
                if not store:
                    raise HTTPException(status_code=404, detail="Loja nao encontrada")
                user.store_id = store.id
        store = self.repository.get_store(user.store_id) if user.store_id else None
        validate_user_store_assignment(user.role, store)
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

    def create_checklist_template(self, payload: ChecklistTemplateCreate) -> ChecklistTemplate:
        title = payload.title.strip()
        if self.repository.get_checklist_template_by_title(title):
            raise HTTPException(status_code=409, detail="Template de checklist ja cadastrado")
        return self.repository.add_checklist_template(
            ChecklistTemplate(
                title=title,
                category=payload.category.strip(),
                store=payload.store.strip() or "Grupo Lia",
                active=True,
            )
        )

    def update_checklist_template(self, template_id: int, payload: ChecklistTemplateUpdate) -> ChecklistTemplate:
        template = self.repository.get_checklist_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template de checklist nao encontrado")

        changes = payload.model_dump(exclude_unset=True)
        if "title" in changes and changes["title"] is not None:
            title = changes["title"].strip()
            existing = self.repository.get_checklist_template_by_title(title)
            if existing and existing.id != template.id:
                raise HTTPException(status_code=409, detail="Template de checklist ja cadastrado")
            template.title = title
        if "category" in changes and changes["category"] is not None:
            template.category = changes["category"].strip()
        if "store" in changes and changes["store"] is not None:
            template.store = changes["store"].strip() or "Grupo Lia"
        if "active" in changes and changes["active"] is not None:
            template.active = changes["active"]

        self.repository.commit()
        refreshed = self.repository.get_checklist_template(template_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Template de checklist nao encontrado")
        return refreshed

    def deactivate_checklist_template(self, template_id: int) -> ChecklistTemplate:
        return self.update_checklist_template(template_id, ChecklistTemplateUpdate(active=False))

    def create_checklist_template_item(
        self, template_id: int, payload: ChecklistTemplateItemCreate
    ) -> ChecklistTemplate:
        template = self.repository.get_checklist_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template de checklist nao encontrado")

        template.items.append(
            ChecklistTemplateItem(
                section=payload.section.strip(),
                text=payload.text.strip(),
                position=self.repository.next_template_item_position(template_id),
                active=True,
            )
        )
        self.repository.commit()
        refreshed = self.repository.get_checklist_template(template_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Template de checklist nao encontrado")
        return refreshed

    def update_checklist_template_item(
        self, item_id: int, payload: ChecklistTemplateItemUpdate
    ) -> ChecklistTemplate:
        item = self.repository.get_checklist_template_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item de template nao encontrado")

        changes = payload.model_dump(exclude_unset=True)
        if "section" in changes and changes["section"] is not None:
            item.section = changes["section"].strip()
        if "text" in changes and changes["text"] is not None:
            item.text = changes["text"].strip()
        if "active" in changes and changes["active"] is not None:
            item.active = changes["active"]

        template_id = item.template_id
        self.repository.commit()
        refreshed = self.repository.get_checklist_template(template_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Template de checklist nao encontrado")
        return refreshed

    def deactivate_checklist_template_item(self, item_id: int) -> ChecklistTemplate:
        return self.update_checklist_template_item(item_id, ChecklistTemplateItemUpdate(active=False))

    def list_manuals(self) -> list[Manual]:
        return self.repository.list_manuals()

    def create_manual(self, payload: ManualCreate) -> Manual:
        unit = payload.unit.strip()
        if self.repository.get_manual_by_unit(unit):
            raise HTTPException(status_code=409, detail="Manual ja cadastrado para esta unidade")

        return self.repository.add_manual(
            Manual(
                unit=unit,
                title=payload.title.strip(),
                temperature=payload.temperature.strip(),
                time_standard=payload.time_standard.strip(),
                critical_point=payload.critical_point.strip(),
                tip=payload.tip.strip(),
                active=True,
            )
        )

    def update_manual(self, manual_id: int, payload: ManualUpdate) -> Manual:
        manual = self.repository.get_manual(manual_id)
        if not manual:
            raise HTTPException(status_code=404, detail="Manual nao encontrado")

        changes = payload.model_dump(exclude_unset=True)
        if "unit" in changes and changes["unit"] is not None:
            unit = changes["unit"].strip()
            existing = self.repository.get_manual_by_unit(unit)
            if existing and existing.id != manual.id:
                raise HTTPException(status_code=409, detail="Manual ja cadastrado para esta unidade")
            manual.unit = unit
        if "title" in changes and changes["title"] is not None:
            manual.title = changes["title"].strip()
        if "temperature" in changes and changes["temperature"] is not None:
            manual.temperature = changes["temperature"].strip()
        if "time_standard" in changes and changes["time_standard"] is not None:
            manual.time_standard = changes["time_standard"].strip()
        if "critical_point" in changes and changes["critical_point"] is not None:
            manual.critical_point = changes["critical_point"].strip()
        if "tip" in changes and changes["tip"] is not None:
            manual.tip = changes["tip"].strip()
        if "active" in changes and changes["active"] is not None:
            manual.active = changes["active"]

        self.repository.commit()
        refreshed = self.repository.get_manual(manual_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Manual nao encontrado")
        return refreshed

    def deactivate_manual(self, manual_id: int) -> Manual:
        return self.update_manual(manual_id, ManualUpdate(active=False))

    def create_manual_section(self, manual_id: int, payload: ManualSectionCreate) -> Manual:
        manual = self.repository.get_manual(manual_id)
        if not manual:
            raise HTTPException(status_code=404, detail="Manual nao encontrado")

        manual.sections.append(
            ManualSection(
                title=payload.title.strip(),
                position=self.repository.next_manual_section_position(manual_id),
                active=True,
            )
        )
        self.repository.commit()
        refreshed = self.repository.get_manual(manual_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Manual nao encontrado")
        return refreshed

    def update_manual_section(self, section_id: int, payload: ManualSectionUpdate) -> Manual:
        section = self.repository.get_manual_section(section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Secao do manual nao encontrada")

        changes = payload.model_dump(exclude_unset=True)
        if "title" in changes and changes["title"] is not None:
            section.title = changes["title"].strip()
        if "active" in changes and changes["active"] is not None:
            section.active = changes["active"]

        manual_id = section.manual_id
        self.repository.commit()
        refreshed = self.repository.get_manual(manual_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Manual nao encontrado")
        return refreshed

    def deactivate_manual_section(self, section_id: int) -> Manual:
        return self.update_manual_section(section_id, ManualSectionUpdate(active=False))

    def create_manual_step(self, section_id: int, payload: ManualStepCreate) -> Manual:
        section = self.repository.get_manual_section(section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Secao do manual nao encontrada")

        section.steps.append(
            ManualStep(
                text=payload.text.strip(),
                position=self.repository.next_manual_step_position(section_id),
                active=True,
            )
        )
        manual_id = section.manual_id
        self.repository.commit()
        refreshed = self.repository.get_manual(manual_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Manual nao encontrado")
        return refreshed

    def update_manual_step(self, step_id: int, payload: ManualStepUpdate) -> Manual:
        step = self.repository.get_manual_step(step_id)
        if not step:
            raise HTTPException(status_code=404, detail="Passo do manual nao encontrado")

        changes = payload.model_dump(exclude_unset=True)
        if "text" in changes and changes["text"] is not None:
            step.text = changes["text"].strip()
        if "active" in changes and changes["active"] is not None:
            step.active = changes["active"]

        manual_id = step.section.manual_id
        self.repository.commit()
        refreshed = self.repository.get_manual(manual_id)
        if not refreshed:
            raise HTTPException(status_code=404, detail="Manual nao encontrado")
        return refreshed

    def deactivate_manual_step(self, step_id: int) -> Manual:
        return self.update_manual_step(step_id, ManualStepUpdate(active=False))
