import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_local_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def get_database_url() -> str:
    load_local_env()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("Define DATABASE_URL en el entorno o en el archivo .env.")
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url
