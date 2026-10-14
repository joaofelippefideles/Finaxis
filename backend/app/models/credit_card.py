from datetime import datetime
from decimal import Decimal

from app.models.base import DATETIME, DECIMAL, ENUM, INT, STR, JsonModel, gen_uuid
from app.models.enums import CardStatus

MONEY = DECIMAL


class CreditCard(JsonModel):
    COLLECTION = "credit_cards"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "name": (STR, None),
        "bank": (STR, None),
        "limit_amount": (DECIMAL, Decimal("0")),
        "closing_day": (INT, 1),
        "due_day": (INT, 1),
        "account_id": (STR, None),
        "status": ((ENUM, CardStatus), CardStatus.active),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }