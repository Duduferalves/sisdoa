"""Configuration settings for SisDoa."""

from __future__ import annotations

import os
from pathlib import Path

# Database configuration
DEFAULT_DB_NAME = "sisdoa.db"
DEFAULT_EXPIRY_THRESHOLD_DAYS = 7

# Get database path from environment or use default
DB_PATH_ENV = os.environ.get("SISDOA_DB_PATH")

if DB_PATH_ENV:
    DATABASE_PATH = Path(DB_PATH_ENV)
else:
    # Default to user's home directory under .sisdoa
    DATA_DIR = Path.home() / ".sisdoa"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH = DATA_DIR / DEFAULT_DB_NAME

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Expiry alert threshold (days)
EXPIRY_THRESHOLD_DAYS = int(
    os.environ.get("SISDOA_EXPIRY_THRESHOLD", DEFAULT_EXPIRY_THRESHOLD_DAYS)
)
