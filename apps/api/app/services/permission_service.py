from __future__ import annotations

from fastapi import HTTPException, status

from ..models import Store, User

Permission = str

ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "admin": {
        "manage_users",
        "manage_stores",
        "manage_manuals",
        "manage_checklists",
        "manage_incidents",
        "view_reports",
        "view_audit",
        "manage_leadership_records",
        "use_ai",
        "upload_evidences",
        "view_evidences",
    },
    "lideranca": {"manage_leadership_records", "view_reports", "view_audit", "view_evidences"},
    "gerente": {
        "manage_checklists",
        "manage_incidents",
        "view_reports",
        "use_ai",
        "upload_evidences",
        "view_evidences",
    },
    "operacao": {"manage_checklists", "manage_incidents", "use_ai", "upload_evidences", "view_evidences"},
    "auditor": {"view_reports", "view_audit", "view_evidences", "use_ai"},
}

GLOBAL_STORE_ROLES = {"admin", "auditor"}


def user_has_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.role, set())


def require_user_permission(user: User, permission: Permission) -> User:
    if not user_has_permission(user, permission):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissao insuficiente")
    return user


def user_has_global_store_access(user: User) -> bool:
    return user.role in GLOBAL_STORE_ROLES


def user_store_name(user: User) -> str | None:
    return user.store.name if user.store else None


def can_access_store(user: User, store_name: str | None) -> bool:
    if user_has_global_store_access(user):
        return True
    own_store = user_store_name(user)
    return bool(own_store and store_name and own_store == store_name)


def require_store_access(user: User, store_name: str | None) -> str | None:
    if user_has_global_store_access(user):
        return store_name

    own_store = user_store_name(user)
    if not own_store:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem loja vinculada")
    if store_name and store_name != own_store:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a loja do usuario")
    return own_store


def validate_user_store_assignment(role: str, store: Store | None) -> None:
    if role in {"gerente", "operacao"} and store is None:
        raise HTTPException(status_code=400, detail="Loja obrigatoria para gerente e operacao")
