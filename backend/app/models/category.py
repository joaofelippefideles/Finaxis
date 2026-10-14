from datetime import datetime

from app.models.base import BOOL, DATETIME, ENUM, STR, JsonModel, gen_uuid
from app.models.enums import CategoryType


class Category(JsonModel):
    COLLECTION = "categories"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "name": (STR, None),
        "type": ((ENUM, CategoryType), None),
        "color": (STR, None),
        "icon": (STR, None),
        "is_default": (BOOL, False),
        "active": (BOOL, True),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }