from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models import User
from ..schemas import ObservabilityStatusRead
from ..security import require_permission
from ..services.observability_service import build_observability_status

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/status", response_model=ObservabilityStatusRead)
def observability_status(_: User = Depends(require_permission("view_audit"))) -> dict:
    return build_observability_status()
