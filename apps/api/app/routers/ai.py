from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Manual, User
from ..schemas import ChatRequest, ChatResponse
from ..security import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


def build_manual_context(db: Session) -> str:
    manuals = db.scalars(select(Manual).order_by(Manual.unit)).all()
    return "\n".join(
        f"{manual.unit}: {manual.title}; temperatura {manual.temperature}; tempo {manual.time_standard}; "
        f"ponto crítico {manual.critical_point}."
        for manual in manuals
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    last_message = payload.messages[-1].content
    context = build_manual_context(db)

    if not settings.gemini_api_key:
        reply = (
            "Modo offline: ainda não há uma chave Gemini configurada no backend. "
            "Mesmo assim, use os manuais técnicos como referência principal. "
            f"Contexto disponível: {context}"
        )
        return ChatResponse(reply=reply, mode="offline")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = (
            "Você é o Assistente Operacional do Grupo Lia. Responda com orientação prática, "
            "objetiva e segura para lojas de pizza, hambúrguer e salgadinhos.\n\n"
            f"Base operacional:\n{context}\n\n"
            f"Pergunta do funcionário:\n{last_message}"
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Não invente regras internas; quando faltar informação, peça confirmação da gestão."
            ),
        )
        return ChatResponse(reply=response.text or "Não consegui responder agora.", mode="gemini")
    except Exception as exc:
        logger.exception("Falha ao consultar Gemini: %s", exc)
        return ChatResponse(
            reply="Não consegui consultar a IA agora. Confira a cota, a chave Gemini e tente novamente.",
            mode="error",
        )
