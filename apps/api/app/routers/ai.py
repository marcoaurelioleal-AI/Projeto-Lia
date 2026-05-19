from __future__ import annotations

from datetime import date
from hashlib import sha256

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import (
    AiChatHistoryItem,
    AiFeedbackCreate,
    AiInteractionRead,
    AiKnowledgeGapRead,
    AiMode,
    AiResponseMode,
    ChatRequest,
    ChatResponse,
)
from ..security import get_current_user, require_permission
from ..services.ai_service import AiService

router = APIRouter(prefix="/ai", tags=["ai"])


def get_ai_service(db: Session = Depends(get_db)) -> AiService:
    return AiService(db)


@router.get("/status")
def ai_status(_: User = Depends(get_current_user)) -> dict[str, str | bool | int | None]:
    key = settings.gemini_api_key or ""
    fingerprint = sha256(key.encode()).hexdigest()[:12] if key else None
    return {
        "configured": bool(key),
        "key_length": len(key) if key else 0,
        "key_fingerprint": fingerprint,
        "model": settings.gemini_model,
    }


@router.get("/history", response_model=list[AiChatHistoryItem])
def ai_history(
    user: User = Depends(get_current_user),
    service: AiService = Depends(get_ai_service),
) -> list[AiChatHistoryItem]:
    return service.history(user)


@router.get("/interactions", response_model=list[AiInteractionRead])
def ai_interactions(
    start_date: date | None = None,
    end_date: date | None = None,
    user_id: int | None = None,
    response_mode: AiResponseMode | None = None,
    ai_mode: AiMode | None = None,
    _: User = Depends(require_permission("view_audit")),
    service: AiService = Depends(get_ai_service),
) -> list[AiInteractionRead]:
    return service.interactions(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        response_mode=response_mode,
        ai_mode=ai_mode,
    )


@router.get("/knowledge-gaps", response_model=list[AiKnowledgeGapRead])
def ai_knowledge_gaps(
    limit: int = 8,
    _: User = Depends(require_permission("view_audit")),
    service: AiService = Depends(get_ai_service),
) -> list[AiKnowledgeGapRead]:
    return service.knowledge_gaps(limit=limit)


@router.post("/interactions/{interaction_id}/feedback", response_model=AiInteractionRead)
def ai_interaction_feedback(
    interaction_id: int,
    payload: AiFeedbackCreate,
    user: User = Depends(get_current_user),
    service: AiService = Depends(get_ai_service),
) -> AiInteractionRead:
    return service.feedback(interaction_id, payload, user)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: User = Depends(require_permission("use_ai")),
    service: AiService = Depends(get_ai_service),
) -> ChatResponse:
    return service.chat(payload, user)
