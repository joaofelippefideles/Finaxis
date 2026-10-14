from datetime import datetime

from app.models.base import BOOL, DATETIME, ENUM, JSON, STR, JsonModel, gen_uuid
from app.models.enums import NotificationType


class Notification(JsonModel):
    COLLECTION = "notifications"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "type": ((ENUM, NotificationType), None),
        "title": (STR, None),
        "message": (STR, None),
        "data": (JSON, dict),
        "is_read": (BOOL, False),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }