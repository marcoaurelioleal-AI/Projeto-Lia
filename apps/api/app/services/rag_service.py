from __future__ import annotations

from collections import Counter
from hashlib import sha256
from math import sqrt
import re
import unicodedata
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AiKnowledgeChunk, Manual, utc_now
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

TOKEN_ALIASES = {
    "armazenamento": {"estoque", "validade", "lote"},
    "balcao": {"atendimento", "loja", "limpeza"},
    "carne": {"hamburguer", "chapa", "burguer"},
    "conferir": {"verificar", "checar", "validar"},
    "cozinha": {"preparo", "higiene", "producao"},
    "delivery": {"entrega", "pedido", "embalagem"},
    "fritadeira": {"fritura", "oleo", "salgados"},
    "fritar": {"fritura", "oleo", "salgados"},
    "fritura": {"fritar", "oleo", "salgados"},
    "hamburguer": {"burguer", "carne", "chapa"},
    "higienizacao": {"limpeza", "utensilios", "contaminacao"},
    "higiene": {"limpeza", "utensilios", "contaminacao"},
    "insumo": {"estoque", "validade", "producao"},
    "insumos": {"estoque", "validade", "producao"},
    "lote": {"validade", "vencimento", "estoque"},
    "oleo": {"fritura", "fritar", "salgados"},
    "pedido": {"atendimento", "delivery", "embalagem"},
    "pizza": {"forno", "massa", "recheio"},
    "preparar": {"preparo", "producao", "cozinha"},
    "temperatura": {"chapa", "forno", "oleo", "seguranca"},
    "validade": {"vencimento", "lote", "estoque"},
    "vencimento": {"validade", "lote", "estoque"},
}

MIN_RELEVANCE_SCORE = 0.15


@dataclass(frozen=True)
class ManualChunk:
    id: str
    source_type: str
    manual_id: int
    section_id: int | None
    unit: str
    title: str
    section_title: str | None
    content: str
    embedding: dict[str, float]


@dataclass(frozen=True)
class RetrievedContext:
    chunk: ManualChunk
    score: float

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
    def score(self, question: str, chunk: ManualChunk, query_embedding: dict[str, float] | None = None) -> float:
        tokens = _tokens(question)
        if not tokens:
            return 0.0

        unit_title_score = 3 * _intersection_count(tokens, f"{chunk.unit} {chunk.title}")
        section_score = 2 * _intersection_count(tokens, chunk.section_title or "")
        content_score = _intersection_count(tokens, chunk.content)
        text_score = unit_title_score + section_score + content_score
        semantic_score = _cosine_similarity(query_embedding or _build_embedding(question), chunk.embedding)
        return float(text_score) + (semantic_score * 4)


class RagService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.manual_repository = ManualRepository(db)
        self.retriever = TextSearchRetriever()

    def retrieve_context(
        self,
        question: str,
        unit: str | None = None,
        limit: int = 5,
    ) -> list[RetrievedContext]:
        manuals = self.manual_repository.list_active_manuals()
        self._sync_knowledge_chunks(self.build_manual_chunks(manuals))
        chunks = self._load_active_chunks(unit=unit)
        query_embedding = _build_embedding(question)

        scored = [
            RetrievedContext(chunk=chunk, score=score)
            for chunk in chunks
            if (score := self.retriever.score(question, chunk, query_embedding)) >= MIN_RELEVANCE_SCORE
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def _sync_knowledge_chunks(self, chunks: list[ManualChunk]) -> None:
        existing = {
            chunk.chunk_key: chunk
            for chunk in self.db.scalars(select(AiKnowledgeChunk).where(AiKnowledgeChunk.source_type == "manual")).all()
        }
        active_keys = {chunk.id for chunk in chunks}

        for chunk in chunks:
            content_hash = sha256(chunk.content.encode("utf-8")).hexdigest()
            row = existing.get(chunk.id)
            if row:
                if row.content_hash != content_hash:
                    row.content = chunk.content
                    row.content_hash = content_hash
                    row.embedding_json = chunk.embedding
                row.manual_id = chunk.manual_id
                row.section_id = chunk.section_id
                row.unit = chunk.unit
                row.title = chunk.title
                row.section_title = chunk.section_title
                row.active = True
                row.updated_at = utc_now()
                continue

            self.db.add(
                AiKnowledgeChunk(
                    chunk_key=chunk.id,
                    source_type=chunk.source_type,
                    manual_id=chunk.manual_id,
                    section_id=chunk.section_id,
                    unit=chunk.unit,
                    title=chunk.title,
                    section_title=chunk.section_title,
                    content=chunk.content,
                    content_hash=content_hash,
                    embedding_json=chunk.embedding,
                    active=True,
                )
            )

        for row in existing.values():
            if row.chunk_key not in active_keys:
                row.active = False
                row.updated_at = utc_now()

        self.db.flush()

    def _load_active_chunks(self, unit: str | None) -> list[ManualChunk]:
        query = select(AiKnowledgeChunk).where(AiKnowledgeChunk.active.is_(True)).order_by(AiKnowledgeChunk.unit)
        if unit:
            query = query.where(AiKnowledgeChunk.unit == unit)

        return [
            ManualChunk(
                id=chunk.chunk_key,
                source_type=chunk.source_type,
                manual_id=chunk.manual_id,
                section_id=chunk.section_id,
                unit=chunk.unit,
                title=chunk.title,
                section_title=chunk.section_title,
                content=chunk.content,
                embedding={key: float(value) for key, value in (chunk.embedding_json or {}).items()},
            )
            for chunk in self.db.scalars(query).all()
        ]

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
                    section_id=None,
                    unit=manual.unit,
                    title=manual.title,
                    section_title=None,
                    content=summary,
                    embedding=_build_embedding(f"{manual.unit} {manual.title} {summary}"),
                )
            )

            for section in manual.sections:
                steps = " ".join(step.text for step in section.steps)
                content = f"Secao: {section.title}. {steps}"
                chunks.append(
                    ManualChunk(
                        id=f"manual:{manual.id}:section:{section.id}",
                        source_type="manual",
                        manual_id=manual.id,
                        section_id=section.id,
                        unit=manual.unit,
                        title=manual.title,
                        section_title=section.title,
                        content=content,
                        embedding=_build_embedding(f"{manual.unit} {manual.title} {content}"),
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


def _build_embedding(text: str) -> dict[str, float]:
    weights: Counter[str] = Counter()
    for token in _tokens(text):
        weights[token] += 1.0
        for alias in TOKEN_ALIASES.get(token, set()):
            weights[alias] += 0.35
    return dict(weights)


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0

    shared = left.keys() & right.keys()
    dot_product = sum(left[token] * right[token] for token in shared)
    if not dot_product:
        return 0.0

    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return dot_product / (left_norm * right_norm)
