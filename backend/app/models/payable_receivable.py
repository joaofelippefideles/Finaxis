from datetime import datetime
from decimal import Decimal

from app.models.base import DATE, DATETIME, DECIMAL, ENUM, STR, JsonModel, gen_uuid
from app.models.enums import ListItemStatus, RecurrenceFrequency

MONEY = DECIMAL


class Payable(JsonModel):
    COLLECTION = "payables"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "description": (STR, None),
        "amount": (DECIMAL, Decimal("0")),
        "due_date": (DATE, None),
        "status": ((ENUM, ListItemStatus), ListItemStatus.pending),
        "category_id": (STR, None),
        "account_id": (STR, None),
        "frequency": ((ENUM, RecurrenceFrequency), None),
        "observation": (STR, None),
        "paid_at": (DATE, None),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }


class Receivable(JsonModel):
    COLLECTION = "receivables"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "description": (STR, None),
        "amount": (DECIMAL, Decimal("0")),
        "due_date": (DATE, None),
        "status": ((ENUM, ListItemStatus), ListItemStatus.pending),
        "category_id": (STR, None),
        "account_id": (STR, None),
        "frequency": ((ENUM, RecurrenceFrequency), None),
        "observation": (STR, None),
        "received_at": (DATE, None),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }