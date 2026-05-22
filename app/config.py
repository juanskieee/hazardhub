"""App configuration."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "hazardhub-stable-secret-key-2024")

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "hazardhub")
    MYSQL_CURSORCLASS = "DictCursor"
    MYSQL_CHARSET = "utf8mb4"

    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    TRAINING_DATA_FILE = str(BASE_DIR / "training_data.json")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
