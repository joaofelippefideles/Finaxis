from pathlib import Path
from typing import Generator

from app.core.config import get_settings
from app.repositories.json_database import JsonDatabase, JsonSession

settings = get_settings()

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (_BACKEND_ROOT / path)


database = JsonDatabase(_resolve(settings.DATA_DIR), _resolve(settings.BACKUP_DIR))

Session = JsonSession
SessionLocal = lambda: JsonSession(database)  # noqa: E731 - fábrica simples


def get_db() -> Generator[JsonSession, None, None]:
    db = JsonSession(database)
    try:
        yield db
    finally:
        db.close()