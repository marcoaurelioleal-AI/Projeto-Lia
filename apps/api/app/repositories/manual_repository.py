from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, with_loader_criteria

from ..models import Manual, ManualSection, ManualStep


class ManualRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active_manuals(self, unit: str | None = None) -> list[Manual]:
        query = (
            select(Manual)
            .where(Manual.active.is_(True))
            .options(
                selectinload(Manual.sections).selectinload(ManualSection.steps),
                with_loader_criteria(ManualSection, ManualSection.active.is_(True)),
                with_loader_criteria(ManualStep, ManualStep.active.is_(True)),
            )
            .order_by(Manual.unit)
        )
        if unit:
            query = query.where(Manual.unit == unit)
        return list(self.db.scalars(query).unique().all())
