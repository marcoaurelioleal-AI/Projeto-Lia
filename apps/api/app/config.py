from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _split_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _clean_env(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1].strip()
    return cleaned or None


def _clean_secret(value: str | None) -> str | None:
    cleaned = _clean_env(value)
    if not cleaned:
        return None
    placeholders = {
        "sua_nova_chave_gemini",
        "sua_chave_api_do_google_gemini_aqui",
        "sua_chave_gemini",
    }
    if cleaned.lower() in placeholders:
        return None
    return cleaned


def _clean_bool(value: str | None, default: bool = False) -> bool:
    cleaned = _clean_env(value)
    if cleaned is None:
        return default
    return cleaned.lower() in {"1", "true", "yes", "on"}


def _database_url(value: str | None) -> str | None:
    cleaned = _clean_env(value)
    if cleaned is None:
        return None
    if cleaned.startswith("postgres://"):
        return cleaned.replace("postgres://", "postgresql+psycopg://", 1)
    if cleaned.startswith("postgresql://"):
        return cleaned.replace("postgresql://", "postgresql+psycopg://", 1)
    return cleaned


def _cookie_samesite(value: str | None) -> str:
    cleaned = (_clean_env(value) or "lax").lower()
    if cleaned not in {"lax", "strict", "none"}:
        return "lax"
    return cleaned


def _is_sqlite_url(value: str) -> bool:
    return value.startswith("sqlite")


def _is_strong_secret(value: str | None, *, min_length: int = 16) -> bool:
    cleaned = _clean_secret(value)
    if not cleaned or len(cleaned) < min_length:
        return False

    weak_values = {
        "admin",
        "admin123",
        "lia-admin",
        "lia-dev-secret-change-me",
        "senha",
        "senha123",
        "troque-essa-senha",
        "troque-esse-segredo",
        "troque-essa-senha-da-lideranca",
    }
    lowered = cleaned.lower()
    if lowered in weak_values or "troque" in lowered or "change-me" in lowered:
        return False

    has_letter = any(char.isalpha() for char in cleaned)
    has_digit = any(char.isdigit() for char in cleaned)
    return has_letter and has_digit


@dataclass(frozen=True)
class Settings:
    app_name: str = "Projeto LIA API"
    app_env: str = _clean_env(os.getenv("APP_ENV") or os.getenv("ENVIRONMENT")) or "development"
    database_url: str = _database_url(os.getenv("DATABASE_URL")) or "sqlite:///./lia.db"
    auto_create_tables: bool = _clean_bool(os.getenv("AUTO_CREATE_TABLES"), default=app_env != "production")
    jwt_secret: str = _clean_env(os.getenv("JWT_SECRET") or os.getenv("SENHA_ACESSO")) or "lia-dev-secret-change-me"
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
    frontend_origins: list[str] = field(default_factory=list)
    gemini_api_key: str | None = _clean_secret(
        os.getenv("GEMINI_API_KEY") or os.getenv("CHAVE_API") or os.getenv("GOOGLE_API_KEY")
    )
    gemini_model: str = _clean_env(os.getenv("MODELO_GEMINI")) or "gemini-2.5-flash"
    default_admin_username: str = _clean_env(os.getenv("LIA_ADMIN_USER")) or "admin"
    default_admin_password: str = _clean_env(os.getenv("LIA_ADMIN_PASSWORD") or os.getenv("SENHA_ACESSO")) or "lia-admin"
    leadership_username: str = _clean_env(os.getenv("LIA_LEADERSHIP_USER")) or "lideranca"
    leadership_password: str | None = _clean_secret(os.getenv("LIA_LEADERSHIP_PASSWORD"))
    session_cookie_secure: bool = _clean_bool(os.getenv("SESSION_COOKIE_SECURE"), default=app_env == "production")
    session_cookie_samesite: str = _cookie_samesite(os.getenv("SESSION_COOKIE_SAMESITE"))
    upload_dir: str = _clean_env(os.getenv("UPLOAD_DIR")) or "data/uploads/checklist-evidences"
    max_upload_bytes: int = int(_clean_env(os.getenv("MAX_UPLOAD_BYTES")) or str(5 * 1024 * 1024))

    def __post_init__(self) -> None:
        origins = os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
        )
        object.__setattr__(self, "frontend_origins", _split_origins(origins))


settings = Settings()


def validate_production_settings(active_settings: Settings = settings) -> None:
    if active_settings.app_env != "production":
        return

    errors: list[str] = []
    if _is_sqlite_url(active_settings.database_url):
        errors.append("DATABASE_URL deve apontar para PostgreSQL em producao")
    if active_settings.auto_create_tables:
        errors.append("AUTO_CREATE_TABLES deve ser false em producao")
    if not _is_strong_secret(active_settings.jwt_secret, min_length=32):
        errors.append("JWT_SECRET deve ser forte em producao")
    if not _is_strong_secret(active_settings.default_admin_password):
        errors.append("LIA_ADMIN_PASSWORD deve ser forte em producao")
    if not _is_strong_secret(active_settings.leadership_password):
        errors.append("LIA_LEADERSHIP_PASSWORD deve ser forte em producao")
    if active_settings.session_cookie_samesite == "none" and not active_settings.session_cookie_secure:
        errors.append("SESSION_COOKIE_SECURE deve ser true quando SESSION_COOKIE_SAMESITE=none")

    if errors:
        raise RuntimeError("Configuracao insegura para producao: " + "; ".join(errors))
