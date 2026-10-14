from datetime import datetime
from decimal import Decimal

from app.models.base import DATE, DATETIME, DECIMAL, ENUM, STR, JsonModel, gen_uuid
from app.models.enums import RecurrenceFrequency, RecurrenceStatus, TransactionType

MONEY = DECIMAL


class RecurringTransaction(JsonModel):
    COLLECTION = "recurring_transactions"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "description": (STR, None),
        "type": ((ENUM, TransactionType), None),
        "amount": (DECIMAL, Decimal("0")),
        "frequency": ((ENUM, RecurrenceFrequency), None),
        "start_date": (DATE, None),
        "end_date": (DATE, None),
        "next_due_date": (DATE, None),
        "category_id": (STR, None),
        "account_id": (STR, None),
        "card_id": (STR, None),
        "status": ((ENUM, RecurrenceStatus), RecurrenceStatus.active),
        "last_generated_at": (DATE, None),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }