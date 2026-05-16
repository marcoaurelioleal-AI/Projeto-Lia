from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

bearer_scheme = HTTPBearer(auto_error=False)
AUTH_COOKIE_NAME = "lia_access_token"
LEADERSHIP_COOKIE_NAME = "lia_leadership_token"


def hash_password(password: str, salt: str | None = None) -> str:
    salt_bytes = base64.urlsafe_b64decode(salt.encode()) if salt else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, 180_000)
    salt_text = base64.urlsafe_b64encode(salt_bytes).decode()
    digest_text = base64.urlsafe_b64encode(digest).decode()
    return f"pbkdf2_sha256${salt_text}${digest_text}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hash_password(password, salt).split("$", 2)[2]
    return hmac.compare_digest(candidate, expected)


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": str(user.id), "username": user.username, "role": user.role, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_leadership_credentials(username: str, password: str) -> bool:
    if not settings.leadership_password:
        return False
    username_ok = hmac.compare_digest(username, settings.leadership_username)
    password_ok = hmac.compare_digest(password, settings.leadership_password)
    return username_ok and password_ok


def create_leadership_access_token() -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": settings.leadership_username,
        "scope": "leadership",
        "role": "leadership",
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def set_session_cookie(response: Response, token: str, *, leadership: bool = False) -> None:
    response.set_cookie(
        key=LEADERSHIP_COOKIE_NAME if leadership else AUTH_COOKIE_NAME,
        value=token,
        max_age=settings.access_token_minutes * 60,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,  # type: ignore[arg-type]
    )


def clear_session_cookie(response: Response, *, leadership: bool = False) -> None:
    response.delete_cookie(
        key=LEADERSHIP_COOKIE_NAME if leadership else AUTH_COOKIE_NAME,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,  # type: ignore[arg-type]
    )


def _token_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    cookie_token: str | None,
) -> str | None:
    if credentials is not None:
        return credentials.credentials
    return cookie_token


def get_current_leadership(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias=LEADERSHIP_COOKIE_NAME),
) -> str:
    token = _token_from_credentials(credentials, cookie_token)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invÃ¡lido") from exc

    if payload.get("scope") != "leadership" or payload.get("sub") != settings.leadership_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a lideranca")
    return settings.leadership_username


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    token = _token_from_credentials(credentials, cookie_token)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    user = db.scalar(select(User).where(User.id == user_id, User.active.is_(True)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou inexistente")
    return user


def require_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a administradores")
    return user
