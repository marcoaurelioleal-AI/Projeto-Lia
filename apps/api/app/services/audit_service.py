from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import jwt
from fastapi import Request
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models import AuditLog, User
from ..security import AUTH_COOKIE_NAME, LEADERSHIP_COOKIE_NAME
from .permission_service import user_has_global_store_access, user_store_name

logger = logging.getLogger("projeto_lia.audit")
AUDITED_METHODS = {"POST", "PATCH", "DELETE"}


@dataclass(frozen=True)
class RequestActor:
    user_id: int | None = None
    username: str | None = None
    role: str | None = None


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        action: str,
        actor_user_id: int | None = None,
        actor_username: str | None = None,
        actor_role: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        store: str | None = None,
        status: str = "success",
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            action=action,
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            actor_role=actor_role,
            entity_type=entity_type,
            entity_id=entity_id,
            store=store,
            status=status,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_logs(
        self,
        *,
        user: User,
        action: str | None = None,
        status: str | None = None,
        entity_type: str | None = None,
        store: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        effective_store = store
        if not user_has_global_store_access(user):
            effective_store = user_store_name(user) or store

        statement = select(AuditLog).order_by(desc(AuditLog.created_at), desc(AuditLog.id)).limit(limit)
        if action:
            statement = statement.where(AuditLog.action == action)
        if status:
            statement = statement.where(AuditLog.status == status)
        if entity_type:
            statement = statement.where(AuditLog.entity_type == entity_type)
        if effective_store:
            statement = statement.where(AuditLog.store == effective_store)
        return list(self.db.scalars(statement))


def record_request_audit(request: Request, *, status_code: int, duration_ms: int, request_id: str) -> None:
    if request.method not in AUDITED_METHODS or not request.url.path.startswith("/api/"):
        return

    actor = _extract_actor(request)
    action = f"{request.method} {request.url.path}"
    status = "success" if status_code < 400 else "failure"
    entity_type, entity_id = _entity_from_path(request.url.path)
    details: dict[str, Any] = {
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": duration_ms,
    }
    if request.url.query:
        details["query"] = request.url.query

    try:
        with SessionLocal() as db:
            AuditService(db).record(
                action=action,
                actor_user_id=actor.user_id,
                actor_username=actor.username,
                actor_role=actor.role,
                entity_type=entity_type,
                entity_id=entity_id,
                status=status,
                request_id=request_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details=details,
            )
    except Exception:
        logger.exception("Nao foi possivel registrar evento de auditoria")


def _extract_actor(request: Request) -> RequestActor:
    token = _request_token(request)
    if not token:
        return RequestActor()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except Exception:
        return RequestActor()

    sub = payload.get("sub")
    user_id = int(sub) if isinstance(sub, str) and sub.isdigit() else None
    return RequestActor(
        user_id=user_id,
        username=payload.get("username") or (sub if isinstance(sub, str) else None),
        role=payload.get("role"),
    )


def _request_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return request.cookies.get(AUTH_COOKIE_NAME) or request.cookies.get(LEADERSHIP_COOKIE_NAME)


def _entity_from_path(path: str) -> tuple[str | None, str | None]:
    segments = [segment for segment in path.split("/") if segment]
    if segments and segments[0] == "api":
        segments = segments[1:]
    entity_type = segments[0] if segments else None
    entity_id = next((segment for segment in segments[1:] if segment.isdigit()), None)
    return entity_type, entity_id
