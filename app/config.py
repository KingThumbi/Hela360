# app/config.py

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(
    dotenv_path=PROJECT_ROOT / ".env",
    override=False,
)


class Config:
    """
    Base application configuration for Hela360.

    Security-sensitive values are loaded from environment variables so
    development, staging and production environments can rotate secrets
    independently.
    """

    # ------------------------------------------------------------------
    # Flask
    # ------------------------------------------------------------------

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-change-me",
    )

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        SECRET_KEY,
    )

    JWT_ALGORITHM = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    JWT_ISSUER = os.getenv(
        "JWT_ISSUER",
        "hela360",
    )

    JWT_AUDIENCE = os.getenv(
        "JWT_AUDIENCE",
        "hela360-api",
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/hela360",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False