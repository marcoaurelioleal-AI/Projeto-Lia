from __future__ import annotations

import logging
from datetime import date, datetime, time
from time import perf_counter

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..models import AiInteraction, User
from ..repositories.ai_repository import AiRepository
from ..schemas import (
    AiChatHistoryItem,
    AiInteractionRead,
    AiMode,
    AiResponseMode,
    ChatRequest,
    ChatResponse,
    ChatSource,
)
from .rag_service import RagService, RetrievedContext

logger = logging.getLogger(__name__)


class AiService:
    def __init__(self, db: Session) -> None:
        self.repository = AiRepository(db)
        self.rag = RagService(db)

    def chat(self, payload: ChatRequest, user: User) -> ChatResponse:
        started_at = perf_counter()
        question = self._last_user_question(payload)
        store = payload.store or "Grupo Lia"
        response_mode = payload.response_mode
        retrieved_context = self.rag.retrieve_context(question=question, unit=payload.unit, limit=5)
        sources = [item.to_source() for item in retrieved_context]
        session = self.repository.get_or_create_session(payload.session_id, user, store, payload.unit, question)

        if not sources:
            reply = (
                "Nao encontrei essa informacao nos manuais disponiveis. Confirme com a gestao antes de executar "
                "esse procedimento."
            )
            latency_ms = self._latency_ms(started_at)
            self._record(
                session=session,
                user=user,
                question=question,
                reply=reply,
                sources=sources,
                ai_mode="offline",
                response_mode=response_mode,
                needs_manager_confirmation=True,
                latency_ms=latency_ms,
                error_message="contexto_insuficiente",
            )
            self._log_safe(user, response_mode, "offline", len(sources), latency_ms)
            return ChatResponse(
                reply=reply,
                mode="offline",
                session_id=session.id,
                sources=sources,
                needs_manager_confirmation=True,
                response_mode=response_mode,
            )

        if not settings.gemini_api_key:
            reply = self._offline_reply(retrieved_context)
            latency_ms = self._latency_ms(started_at)
            self._record(
                session=session,
                user=user,
                question=question,
                reply=reply,
                sources=sources,
                ai_mode="offline",
                response_mode=response_mode,
                needs_manager_confirmation=True,
                latency_ms=latency_ms,
            )
            self._log_safe(user, response_mode, "offline", len(sources), latency_ms)
            return ChatResponse(
                reply=reply,
                mode="offline",
                session_id=session.id,
                sources=sources,
                needs_manager_confirmation=True,
                response_mode=response_mode,
            )

        try:
            reply = self._ask_gemini(
                question=question,
                store=store,
                unit=payload.unit,
                response_mode=response_mode,
                retrieved_context=retrieved_context,
            )
            latency_ms = self._latency_ms(started_at)
            self._record(
                session=session,
                user=user,
                question=question,
                reply=reply,
                sources=sources,
                ai_mode="gemini",
                response_mode=response_mode,
                needs_manager_confirmation=False,
                latency_ms=latency_ms,
            )
            self._log_safe(user, response_mode, "gemini", len(sources), latency_ms)
            return ChatResponse(
                reply=reply,
                mode="gemini",
                session_id=session.id,
                sources=sources,
                needs_manager_confirmation=False,
                response_mode=response_mode,
            )
        except Exception as exc:
            logger.exception("Falha ao consultar Gemini: %s", exc)
            reply = describe_gemini_error(exc)
            latency_ms = self._latency_ms(started_at)
            self._record(
                session=session,
                user=user,
                question=question,
                reply=reply,
                sources=sources,
                ai_mode="error",
                response_mode=response_mode,
                needs_manager_confirmation=True,
                latency_ms=latency_ms,
                error_message=str(exc),
            )
            self._log_safe(user, response_mode, "error", len(sources), latency_ms)
            return ChatResponse(
                reply=reply,
                mode="error",
                session_id=session.id,
                sources=sources,
                needs_manager_confirmation=True,
                response_mode=response_mode,
            )

    def history(self, user: User) -> list[AiChatHistoryItem]:
        logs = self.repository.list_chat_logs(user=user, limit=8)
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

    def interactions(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        user_id: int | None = None,
        response_mode: AiResponseMode | None = None,
        ai_mode: AiMode | None = None,
    ) -> list[AiInteractionRead]:
        start_at = datetime.combine(start_date, time.min) if start_date else None
        end_at = datetime.combine(end_date, time.max) if end_date else None
        interactions = self.repository.list_interactions(
            start_at=start_at,
            end_at=end_at,
            user_id=user_id,
            response_mode=response_mode,
            ai_mode=ai_mode,
        )
        return [self._serialize_interaction(interaction) for interaction in interactions]

    def _ask_gemini(
        self,
        question: str,
        store: str,
        unit: str | None,
        response_mode: AiResponseMode,
        retrieved_context: list[RetrievedContext],
    ) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = self._build_prompt(
            question=question,
            store=store,
            unit=unit,
            response_mode=response_mode,
            retrieved_context=retrieved_context,
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Voce e a Lia, assistente operacional interna do Grupo Lia. Use apenas a base operacional "
                    "fornecida. Se faltar informacao, peca confirmacao da gestao. Nao prometa executar acoes."
                )
            ),
        )
        return response.text or "Nao consegui responder agora. Confirme com a gestao antes de seguir."

    def _build_prompt(
        self,
        question: str,
        store: str,
        unit: str | None,
        response_mode: AiResponseMode,
        retrieved_context: list[RetrievedContext],
    ) -> str:
        mode_instructions = {
            "rapido": "Responda em no maximo 5 linhas, de forma direta e operacional.",
            "detalhado": "Explique em passo a passo, cite cuidados e indique quando chamar a gestao.",
            "treinamento": "Use linguagem didatica para funcionario novo e explique o motivo da regra.",
        }
        context = "\n\n".join(
            (
                f"Fonte {index}: {item.chunk.unit} / {item.chunk.title}"
                f"{f' / {item.chunk.section_title}' if item.chunk.section_title else ''}\n"
                f"{item.chunk.content}"
            )
            for index, item in enumerate(retrieved_context, start=1)
        )[:5000]

        return (
            "Voce responde como Assistente Operacional do Grupo Lia para loja, cozinha, balcao e delivery.\n"
            "Use apenas a base operacional recuperada. Nao invente regra interna.\n"
            "Quando a informacao nao estiver clara nos manuais, diga para confirmar com a gestao.\n"
            "Priorize seguranca alimentar, temperatura, validade, higiene e padronizacao.\n"
            f"Modo de resposta: {response_mode}. {mode_instructions[response_mode]}\n"
            f"Loja: {store}\nUnidade filtrada: {unit or 'Todas'}\n\n"
            f"Base operacional recuperada:\n{context}\n\n"
            f"Pergunta do funcionario:\n{question}"
        )

    def _offline_reply(self, retrieved_context: list[RetrievedContext]) -> str:
        context = "\n".join(
            (
                f"Fonte: {item.chunk.unit} / {item.chunk.title}"
                f"{f' / {item.chunk.section_title}' if item.chunk.section_title else ''}\n"
                f"Trecho: {item.chunk.content[:500]}"
            )
            for item in retrieved_context
        )
        return (
            "Sou a Lia, mas estou em modo offline porque a chave Gemini ainda nao esta ativa no backend. "
            "Nao consultei IA externa agora. Use os manuais internos abaixo como referencia principal e confirme "
            f"com a gestao quando a duvida envolver decisao operacional.\n\n{context}"
        )

    def _record(
        self,
        session,
        user: User,
        question: str,
        reply: str,
        sources: list[ChatSource],
        ai_mode: AiMode,
        response_mode: AiResponseMode,
        needs_manager_confirmation: bool,
        latency_ms: int,
        error_message: str | None = None,
    ) -> None:
        sources_json = [source.model_dump() for source in sources]
        self.repository.add_chat_log(
            session=session,
            user=user,
            question=question,
            reply=reply,
            sources=sources_json,
            mode=ai_mode,
            needs_manager_confirmation=needs_manager_confirmation,
        )
        self.repository.add_interaction(
            user=user,
            question=question,
            answer=reply,
            response_mode=response_mode,
            ai_mode=ai_mode,
            sources=sources_json,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        self.repository.commit()

    @staticmethod
    def _last_user_question(payload: ChatRequest) -> str:
        for message in reversed(payload.messages):
            if message.role == "user":
                question = message.content.strip()
                if not question:
                    break
                return question[:2000]
        raise HTTPException(status_code=400, detail="Pergunta da IA nao pode ser vazia")

    @staticmethod
    def _latency_ms(started_at: float) -> int:
        return round((perf_counter() - started_at) * 1000)

    @staticmethod
    def _serialize_interaction(interaction: AiInteraction) -> AiInteractionRead:
        return AiInteractionRead(
            id=interaction.id,
            user_id=interaction.user_id,
            user_name=interaction.user.name if interaction.user else None,
            question=interaction.question,
            answer=interaction.answer,
            response_mode=interaction.response_mode,
            ai_mode=interaction.ai_mode,
            sources=[ChatSource(**source) for source in (interaction.sources_json or [])],
            created_at=interaction.created_at,
            error_message=interaction.error_message,
            latency_ms=interaction.latency_ms,
        )

    @staticmethod
    def _log_safe(user: User, response_mode: str, ai_mode: str, sources_count: int, latency_ms: int) -> None:
        logger.info(
            "ai_interaction user_id=%s response_mode=%s ai_mode=%s sources=%s latency_ms=%s",
            user.id,
            response_mode,
            ai_mode,
            sources_count,
            latency_ms,
        )


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
