from datetime import datetime
from decimal import Decimal

from app.models.base import DATETIME, DECIMAL, STR, JsonModel, gen_uuid

MONEY = DECIMAL


class Budget(JsonModel):
    """Orçamento mensal por categoria. month = 'YYYY-MM' ou NULL (vigência contínua)."""

    COLLECTION = "budgets"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "category_id": (STR, None),
        "limit_amount": (DECIMAL, Decimal("0")),
        "month": (STR, None),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }