from datetime import datetime

from app.models.base import BOOL, DATETIME, STR, JsonModel, gen_uuid

# Compatibilidade com imports antigos (``from app.models.user import gen_uuid``).
__all__ = ["User", "gen_uuid"]


class User(JsonModel):
    COLLECTION = "users"
    _fields = {
        "id": (STR, gen_uuid),
        "name": (STR, None),
        "email": (STR, None),
        "password_hash": (STR, None),
        "currency": (STR, "BRL"),
        "date_format": (STR, "DD/MM/YYYY"),
        "locale": (STR, "pt-BR"),
        "is_active": (BOOL, True),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }