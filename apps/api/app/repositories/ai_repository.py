from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models import AiChatLog, AiChatSession, AiInteraction, User, utc_now


class AiRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_session(
        self,
        session_id: int | None,
        user: User,
        store: str,
        unit: str | None,
        question: str,
    ) -> AiChatSession:
        if session_id:
            session = self.db.scalar(
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
        self.db.add(session)
        self.db.flush()
        return session

    def add_chat_log(
        self,
        session: AiChatSession,
        user: User,
        question: str,
        reply: str,
        sources: list[dict[str, str | int | None]],
        mode: str,
        needs_manager_confirmation: bool,
    ) -> None:
        session.updated_at = utc_now()
        self.db.add(
            AiChatLog(
                session_id=session.id,
                user_id=user.id,
                question=question[:4000],
                answer_summary=reply[:1000],
                sources=sources,
                mode=mode,
                needs_manager_confirmation=needs_manager_confirmation,
            )
        )

    def add_interaction(
        self,
        user: User,
        question: str,
        answer: str,
        response_mode: str,
        ai_mode: str,
        sources: list[dict[str, str | int | None]],
        latency_ms: int,
        needs_manager_confirmation: bool,
        error_message: str | None = None,
    ) -> AiInteraction:
        interaction = AiInteraction(
            user_id=user.id,
            question=question[:4000],
            answer=answer[:8000],
            response_mode=response_mode,
            ai_mode=ai_mode,
            sources_json=sources,
            latency_ms=latency_ms,
            needs_manager_confirmation=needs_manager_confirmation,
            error_message=error_message[:2000] if error_message else None,
        )
        self.db.add(interaction)
        return interaction

    def get_interaction(self, interaction_id: int) -> AiInteraction | None:
        return self.db.scalar(
            select(AiInteraction).options(joinedload(AiInteraction.user)).where(AiInteraction.id == interaction_id)
        )

    def list_chat_logs(self, user: User, limit: int = 8) -> list[AiChatLog]:
        query = (
            select(AiChatLog)
            .join(AiChatSession)
            .options(joinedload(AiChatLog.session))
            .order_by(AiChatLog.created_at.desc())
            .limit(limit)
        )
        if user.role != "admin":
            query = query.where(AiChatLog.user_id == user.id)
        return list(self.db.scalars(query).all())

    def list_interactions(
        self,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        user_id: int | None = None,
        response_mode: str | None = None,
        ai_mode: str | None = None,
        limit: int = 80,
    ) -> list[AiInteraction]:
        query = select(AiInteraction).options(joinedload(AiInteraction.user)).order_by(AiInteraction.created_at.desc())
        if start_at:
            query = query.where(AiInteraction.created_at >= start_at)
        if end_at:
            query = query.where(AiInteraction.created_at <= end_at)
        if user_id:
            query = query.where(AiInteraction.user_id == user_id)
        if response_mode:
            query = query.where(AiInteraction.response_mode == response_mode)
        if ai_mode:
            query = query.where(AiInteraction.ai_mode == ai_mode)
        return list(self.db.scalars(query.limit(limit)).all())

    def set_feedback(self, interaction: AiInteraction, rating: str, comment: str | None) -> AiInteraction:
        interaction.feedback_rating = rating
        interaction.feedback_comment = comment[:1200] if comment else None
        interaction.feedback_created_at = utc_now()
        self.db.flush()
        return interaction

    def commit(self) -> None:
        self.db.commit()
