from __future__ import annotations

import logging
from hashlib import sha256

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..database import get_db
from ..manual_knowledge import ManualKnowledgeService
from ..models import AiChatLog, AiChatSession, User, utc_now
from ..schemas import AiChatHistoryItem, ChatRequest, ChatResponse, ChatSource
from ..security import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


def describe_gemini_error(exc: Exception) -> str:
    error_text = str(exc)
    normalized = error_text.upper()

    if "API_KEY_INVALID" in normalized or "API KEY NOT VALID" in normalized or "INVALID_ARGUMENT" in normalized:
        return "A chave Gemini configurada no servidor e invalida. Gere uma nova chave e atualize GEMINI_API_KEY."
    if "API_KEY_SERVICE_BLOCKED" in normalized or "SERVICE_DISABLED" in normalized:
        return "A chave Gemini existe, mas a API do Gemini/Generative Language nao esta habilitada para ela."
    if "API_KEY_HTTP_REFERRER_BLOCKED" in normalized or "API_KEY_IP_ADDRESS_BLOCKED" in normalized:
        return "A chave Gemini esta com restricao de uso. Para backend, ajuste as restricoes da chave."
    if "RESOURCE_EXHAUSTED" in normalized or "QUOTA" in normalized or "429" in normalized:
        return "A cota do Gemini foi atingida ou esta temporariamente limitada. Verifique a cota no Google AI Studio."
    if "MODEL_NOT_FOUND" in normalized or "NOT_FOUND" in normalized:
        return f"O modelo {settings.gemini_model} nao esta disponivel para essa chave. Tente MODELO_GEMINI=gemini-1.5-flash."
    if "PERMISSION_DENIED" in normalized or "403" in normalized:
        return "A chave Gemini nao tem permissao para essa chamada. Verifique restricoes, projeto Google e API habilitada."
    return "Nao consegui consultar o Gemini agora. Veja os logs do servidor para o detalhe tecnico da falha."


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
    db: Session = Depends(get_db),
) -> list[AiChatHistoryItem]:
    query = (
        select(AiChatLog)
        .join(AiChatSession)
        .options(selectinload(AiChatLog.session))
        .order_by(AiChatLog.created_at.desc())
        .limit(8)
    )
    if user.role != "admin":
        query = query.where(AiChatLog.user_id == user.id)

    logs = db.scalars(query).all()
    return [
        AiChatHistoryItem(
            id=log.id,
            session_id=log.session_id,
            store=log.session.store,
            unit=log.session.unit,
            question=log.question,
            answer_summary=log.answer_summary,
            sources=[ChatSource(**source) for source in (log.sources or [])],
            mode=log.mode,
            needs_manager_confirmation=log.needs_manager_confirmation,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    last_message = payload.messages[-1].content
    store = payload.store or "Grupo Lia"
    knowledge = ManualKnowledgeService(db).build(last_message, payload.unit)
    session = get_or_create_session(db, payload.session_id, user, store, payload.unit, last_message)

    if not settings.gemini_api_key:
        reply = (
            "Sou a Lia, mas estou em modo offline porque a chave Gemini ainda nao esta ativa no backend. "
            "Use os manuais internos como referencia principal e confirme com a gestao quando a duvida envolver "
            f"decisao operacional. Base encontrada: {knowledge.context}"
        )
        save_chat_log(db, session, user, last_message, reply, knowledge.sources, "offline", True)
        return ChatResponse(
            reply=reply,
            mode="offline",
            session_id=session.id,
            sources=knowledge.sources,
            needs_manager_confirmation=True,
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = (
            "Voce e a Lia, assistente operacional interna da Central LIA. Responda em portugues do Brasil, "
            "com orientacao pratica, objetiva e segura para lojas de pizza, hamburguer e salgadinhos. "
            "Use somente a base operacional fornecida. Nao invente regras internas. Priorize seguranca alimentar, "
            "validade, limpeza, padronizacao e confirmacao com a gestao quando faltar informacao.\n\n"
            f"Loja: {store}\nUnidade filtrada: {payload.unit or 'Todas'}\n"
            f"Base operacional:\n{knowledge.context}\n\n"
            f"Pergunta do funcionario:\n{last_message}"
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Responda como Lia. Se a base nao for suficiente, diga claramente para confirmar com a gestao. "
                    "Nao prometa executar acoes no sistema."
                )
            ),
        )
        reply = response.text or "Nao consegui responder agora. Confirme com a gestao antes de seguir."
        save_chat_log(
            db,
            session,
            user,
            last_message,
            reply,
            knowledge.sources,
            "gemini",
            knowledge.needs_manager_confirmation,
        )
        return ChatResponse(
            reply=reply,
            mode="gemini",
            session_id=session.id,
            sources=knowledge.sources,
            needs_manager_confirmation=knowledge.needs_manager_confirmation,
        )
    except Exception as exc:
        logger.exception("Falha ao consultar Gemini: %s", exc)
        reply = describe_gemini_error(exc)
        save_chat_log(db, session, user, last_message, reply, knowledge.sources, "error", True)
        return ChatResponse(
            reply=reply,
            mode="error",
            session_id=session.id,
            sources=knowledge.sources,
            needs_manager_confirmation=True,
        )


def get_or_create_session(
    db: Session,
    session_id: int | None,
    user: User,
    store: str,
    unit: str | None,
    question: str,
) -> AiChatSession:
    if session_id:
        session = db.scalar(
            select(AiChatSession).where(AiChatSession.id == session_id, AiChatSession.user_id == user.id)
        )
        if session:
            return session

    session = AiChatSession(
        user_id=user.id,
        store=store,
        unit=unit,
        title=question[:150],
    )
    db.add(session)
    db.flush()
    return session


def save_chat_log(
    db: Session,
    session: AiChatSession,
    user: User,
    question: str,
    reply: str,
    sources: list[ChatSource],
    mode: str,
    needs_manager_confirmation: bool,
) -> None:
    session.updated_at = utc_now()
    db.add(
        AiChatLog(
            session_id=session.id,
            user_id=user.id,
            question=question[:4000],
            answer_summary=reply[:1000],
            sources=[source.model_dump() for source in sources],
            mode=mode,
            needs_manager_confirmation=needs_manager_confirmation,
        )
    )
    db.commit()
