from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ExecutiveDashboardRead, ReportSummaryRead
from ..security import get_current_user
from ..services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


@router.get("/summary", response_model=ReportSummaryRead)
def get_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    store: str | None = None,
    user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportSummaryRead:
    target_end = end_date or date.today()
    target_start = start_date or (target_end - timedelta(days=6))
    return service.summary(start_date=target_start, end_date=target_end, user=user, store=store)


@router.get("/executive", response_model=ExecutiveDashboardRead)
def get_executive_dashboard(
    user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ExecutiveDashboardRead:
    return service.executive_dashboard(user=user)
