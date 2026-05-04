from __future__ import annotations

import logging
from hashlib import sha256

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


def describe_gemini_error(exc: Exception) -> str:
    error_text = str(exc)
    normalized = error_text.upper()

    if "API_KEY_INVALID" in normalized or "API KEY NOT VALID" in normalized:
        return "A chave Gemini configurada no servidor é inválida. Gere uma nova chave e atualize GEMINI_API_KEY no Render."
    if "API_KEY_SERVICE_BLOCKED" in normalized or "SERVICE_DISABLED" in normalized:
        return "A chave Gemini existe, mas a API do Gemini/Generative Language não está habilitada para ela."
    if "API_KEY_HTTP_REFERRER_BLOCKED" in normalized or "API_KEY_IP_ADDRESS_BLOCKED" in normalized:
        return "A chave Gemini está com restrição de uso. Para backend no Render, ajuste as restrições da chave ou use uma chave sem restrição de referer."
    if "RESOURCE_EXHAUSTED" in normalized or "QUOTA" in normalized or "429" in normalized:
        return "A cota do Gemini foi atingida ou está temporariamente limitada. Aguarde ou verifique o billing/cota no Google AI Studio."
    if "MODEL_NOT_FOUND" in normalized or "NOT_FOUND" in normalized:
        return f"O modelo {settings.gemini_model} não está disponível para essa chave. Tente MODELO_GEMINI=gemini-1.5-flash."
    if "PERMISSION_DENIED" in normalized or "403" in normalized:
        return "A chave Gemini não tem permissão para essa chamada. Verifique restrições, projeto Google e API habilitada."
    return "Não consegui consultar a IA agora. Veja os logs do Render para o detalhe técnico da falha Gemini."


def build_manual_context(db: Session) -> str:
    manuals = db.scalars(select(Manual).order_by(Manual.unit)).all()
    return "\n".join(
        f"{manual.unit}: {manual.title}; temperatura {manual.temperature}; tempo {manual.time_standard}; "
        f"ponto crítico {manual.critical_point}."
        for manual in manuals
    )


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
            reply=describe_gemini_error(exc),
            mode="error",
        )
