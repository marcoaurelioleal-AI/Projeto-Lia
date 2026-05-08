from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import Manual, ManualSection
from .schemas import ChatSource


STOPWORDS = {
    "a",
    "ao",
    "as",
    "com",
    "da",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "na",
    "no",
    "o",
    "os",
    "para",
    "por",
    "qual",
    "quais",
    "que",
    "um",
    "uma",
}


@dataclass(frozen=True)
class ManualKnowledge:
    context: str
    sources: list[ChatSource]
    needs_manager_confirmation: bool


class ManualKnowledgeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, question: str, unit: str | None = None) -> ManualKnowledge:
        manuals = self._load_manuals(unit)
        sources = self._rank_sources(manuals, question)
        needs_manager_confirmation = len(sources) == 0
        context_sources = sources or self._fallback_sources(manuals)
        context = "\n".join(
            (
                f"Fonte: {source.unit} / {source.manual_title}"
                f"{f' / {source.section_title}' if source.section_title else ''}\n"
                f"Trecho: {source.excerpt}"
            )
            for source in context_sources
        )
        return ManualKnowledge(
            context=context or "Nenhum manual interno encontrado.",
            sources=sources,
            needs_manager_confirmation=needs_manager_confirmation,
        )

    def _load_manuals(self, unit: str | None) -> list[Manual]:
        query = select(Manual).options(selectinload(Manual.sections).selectinload(ManualSection.steps)).order_by(Manual.unit)
        if unit:
            query = query.where(Manual.unit == unit)
        return list(self.db.scalars(query).unique().all())

    def _rank_sources(self, manuals: list[Manual], question: str) -> list[ChatSource]:
        tokens = _tokens(question)
        if not tokens:
            return []

        scored: list[tuple[int, ChatSource]] = []
        for manual in manuals:
            manual_source = ChatSource(
                manual_id=manual.id,
                unit=manual.unit,
                manual_title=manual.title,
                section_title=None,
                excerpt=(
                    f"Temperatura: {manual.temperature}. Tempo: {manual.time_standard}. "
                    f"Ponto critico: {manual.critical_point}. Dica: {manual.tip}"
                ),
            )
            manual_score = _score(manual_source.excerpt, tokens) + _score(f"{manual.unit} {manual.title}", tokens)
            if manual_score:
                scored.append((manual_score, manual_source))

            for section in manual.sections:
                excerpt = " ".join(step.text for step in section.steps)
                source = ChatSource(
                    manual_id=manual.id,
                    unit=manual.unit,
                    manual_title=manual.title,
                    section_title=section.title,
                    excerpt=excerpt[:500],
                )
                section_score = _score(f"{section.title} {excerpt}", tokens) + _score(f"{manual.unit} {manual.title}", tokens)
                if section_score:
                    scored.append((section_score, source))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [source for _, source in scored[:5]]

    def _fallback_sources(self, manuals: list[Manual]) -> list[ChatSource]:
        return [
            ChatSource(
                manual_id=manual.id,
                unit=manual.unit,
                manual_title=manual.title,
                section_title=None,
                excerpt=f"Ponto critico: {manual.critical_point}. Dica: {manual.tip}",
            )
            for manual in manuals[:3]
        ]


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return {token for token in re.findall(r"[a-z0-9]{3,}", ascii_text) if token not in STOPWORDS}


def _score(text: str, tokens: set[str]) -> int:
    haystack = _tokens(text)
    return len(tokens & haystack)
