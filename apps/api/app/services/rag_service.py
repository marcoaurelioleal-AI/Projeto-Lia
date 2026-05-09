from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import Manual
from ..repositories.manual_repository import ManualRepository
from ..schemas import ChatSource

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
class ManualChunk:
    id: str
    source_type: str
    manual_id: int
    unit: str
    title: str
    section_title: str | None
    content: str


@dataclass(frozen=True)
class RetrievedContext:
    chunk: ManualChunk
    score: int

    def to_source(self) -> ChatSource:
        return ChatSource(
            source_type=self.chunk.source_type,
            manual_id=self.chunk.manual_id,
            unit=self.chunk.unit,
            manual_title=self.chunk.title,
            title=self.chunk.title,
            section_title=self.chunk.section_title,
            excerpt=self.chunk.content[:500],
        )


class TextSearchRetriever:
    def score(self, question: str, chunk: ManualChunk) -> int:
        tokens = _tokens(question)
        if not tokens:
            return 0

        unit_title_score = 3 * _intersection_count(tokens, f"{chunk.unit} {chunk.title}")
        section_score = 2 * _intersection_count(tokens, chunk.section_title or "")
        content_score = _intersection_count(tokens, chunk.content)
        return unit_title_score + section_score + content_score


class RagService:
    def __init__(self, db: Session) -> None:
        self.manual_repository = ManualRepository(db)
        self.retriever = TextSearchRetriever()

    def retrieve_context(
        self,
        question: str,
        unit: str | None = None,
        limit: int = 5,
    ) -> list[RetrievedContext]:
        manuals = self.manual_repository.list_active_manuals(unit=unit)
        chunks = self.build_manual_chunks(manuals)

        scored = [
            RetrievedContext(chunk=chunk, score=score)
            for chunk in chunks
            if (score := self.retriever.score(question, chunk)) > 0
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        # TODO: trocar TextSearchRetriever por embeddings/vector store quando a base de documentos crescer.
        return scored[:limit]

    @staticmethod
    def build_manual_chunks(manuals: list[Manual]) -> list[ManualChunk]:
        chunks: list[ManualChunk] = []
        for manual in manuals:
            summary = (
                f"Unidade: {manual.unit}. Manual: {manual.title}. "
                f"Temperatura: {manual.temperature}. Tempo padrao: {manual.time_standard}. "
                f"Ponto critico: {manual.critical_point}. Dica: {manual.tip}."
            )
            chunks.append(
                ManualChunk(
                    id=f"manual:{manual.id}:summary",
                    source_type="manual",
                    manual_id=manual.id,
                    unit=manual.unit,
                    title=manual.title,
                    section_title=None,
                    content=summary,
                )
            )

            for section in manual.sections:
                steps = " ".join(step.text for step in section.steps)
                chunks.append(
                    ManualChunk(
                        id=f"manual:{manual.id}:section:{section.id}",
                        source_type="manual",
                        manual_id=manual.id,
                        unit=manual.unit,
                        title=manual.title,
                        section_title=section.title,
                        content=f"Secao: {section.title}. {steps}",
                    )
                )
        return chunks


def retrieve_relevant_manual_context(
    db: Session,
    question: str,
    limit: int = 5,
    unit: str | None = None,
) -> list[RetrievedContext]:
    return RagService(db).retrieve_context(question=question, unit=unit, limit=limit)


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return {token for token in re.findall(r"[a-z0-9]{3,}", ascii_text) if token not in STOPWORDS}


def _intersection_count(tokens: set[str], text: str) -> int:
    return len(tokens & _tokens(text))
