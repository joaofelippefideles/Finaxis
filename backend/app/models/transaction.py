from datetime import datetime
from decimal import Decimal

from app.models.base import (
    BOOL,
    DATE,
    DATETIME,
    DECIMAL,
    ENUM,
    INT,
    STR,
    JsonModel,
    gen_uuid,
)
from app.models.enums import TransactionStatus, TransactionType

MONEY = DECIMAL


class Transaction(JsonModel):
    COLLECTION = "transactions"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "type": ((ENUM, TransactionType), None),
        "status": ((ENUM, TransactionStatus), TransactionStatus.pending),
        "description": (STR, None),
        "amount": (DECIMAL, Decimal("0")),
        "date": (DATE, None),
        "category_id": (STR, None),
        "account_id": (STR, None),
        "from_account_id": (STR, None),
        "to_account_id": (STR, None),
        "card_id": (STR, None),
        "installment_id": (STR, None),
        "installment_number": (INT, None),
        "installments_total": (INT, None),
        "recurring_id": (STR, None),
        "observation": (STR, None),
        "paid_at": (DATE, None),
        "is_installment": (BOOL, False),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }