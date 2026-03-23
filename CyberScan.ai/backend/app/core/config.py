"""
Application Configuration using Pydantic Settings.
All values loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────
    APP_NAME: str = "CyberScan.Ai"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "changeme-use-a-strong-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Database ─────────────────────────────────────────────────────
    POSTGRES_PASSWORD: str = "securescout_dev_password"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/securescout"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/securescout"

    # ── Redis ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Groq (Free AI) ────────────────────────────────────────────────
    GROQ_API_KEY: str = ""

    # ── Admin Bootstrap ───────────────────────────────────────────────
    BOOTSTRAP_SECRET: str = ""

    # ── Email (Brevo HTTP API — works on Render free tier) ───────────
    BREVO_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@cyberscan.ai"
    RESEND_API_KEY: str = ""
    # Legacy SMTP (not used on Render — ports blocked)
    SMTP_HOST: str = "smtp-relay.brevo.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # ── CORS / Security ───────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80", "https://cyberscan-ai-app.netlify.app"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # ── Scan Limits ───────────────────────────────────────────────────
    FREE_SCANS_PER_DAY: int = 999
    PRO_SCANS_PER_DAY: int = 999

    # ── Frontend ─────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = {
        "env_file": ["../../.env", "../.env", ".env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "env_nested_delimiter": "__",
    }


settings = Settings()
