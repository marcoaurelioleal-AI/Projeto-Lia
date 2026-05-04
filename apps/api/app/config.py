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


@dataclass(frozen=True)
class Settings:
    app_name: str = "Projeto LIA API"
    database_url: str = _clean_env(os.getenv("DATABASE_URL")) or "sqlite:////app/data/lia.db"
    jwt_secret: str = _clean_env(os.getenv("JWT_SECRET") or os.getenv("SENHA_ACESSO")) or "lia-dev-secret-change-me"
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
    frontend_origins: list[str] = field(default_factory=list)
    gemini_api_key: str | None = _clean_env(
        os.getenv("GEMINI_API_KEY") or os.getenv("CHAVE_API") or os.getenv("GOOGLE_API_KEY")
    )
    gemini_model: str = _clean_env(os.getenv("MODELO_GEMINI")) or "gemini-2.5-flash"
    default_admin_username: str = _clean_env(os.getenv("LIA_ADMIN_USER")) or "admin"
    default_admin_password: str = _clean_env(os.getenv("LIA_ADMIN_PASSWORD") or os.getenv("SENHA_ACESSO")) or "lia-admin"

    def __post_init__(self) -> None:
        origins = os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
        )
        object.__setattr__(self, "frontend_origins", _split_origins(origins))


settings = Settings()
