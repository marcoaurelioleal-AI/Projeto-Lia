from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import ChecklistRun, ChecklistRunItem


class ChecklistRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_runs_for_date(self, run_date: date, store: str) -> list[ChecklistRun]:
        return list(
            self.db.scalars(
                select(ChecklistRun)
                .options(
                    selectinload(ChecklistRun.template),
                    selectinload(ChecklistRun.items).selectinload(ChecklistRunItem.template_item),
                    selectinload(ChecklistRun.items).selectinload(ChecklistRunItem.completed_by),
                )
                .where(ChecklistRun.run_date == run_date, ChecklistRun.store == store)
                .order_by(ChecklistRun.id)
            ).all()
        )

    def get_run(self, run_id: int) -> ChecklistRun | None:
        return self.db.scalar(
            select(ChecklistRun)
            .options(
                selectinload(ChecklistRun.template),
                selectinload(ChecklistRun.items).selectinload(ChecklistRunItem.template_item),
                selectinload(ChecklistRun.items).selectinload(ChecklistRunItem.completed_by),
            )
            .where(ChecklistRun.id == run_id)
        )

    def get_run_item(self, run_id: int, item_id: int) -> ChecklistRunItem | None:
        return self.db.scalar(
            select(ChecklistRunItem)
            .options(selectinload(ChecklistRunItem.run), selectinload(ChecklistRunItem.template_item))
            .where(ChecklistRunItem.id == item_id, ChecklistRunItem.run_id == run_id)
        )

    def commit(self) -> None:
        self.db.commit()
