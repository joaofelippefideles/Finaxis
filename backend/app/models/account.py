from datetime import datetime
from decimal import Decimal

from app.models.base import BOOL, DATETIME, DECIMAL, ENUM, STR, JsonModel, gen_uuid
from app.models.enums import AccountType

MONEY = DECIMAL


class Account(JsonModel):
    COLLECTION = "accounts"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "name": (STR, None),
        "bank": (STR, None),
        "type": ((ENUM, AccountType), AccountType.checking),
        "initial_balance": (DECIMAL, Decimal("0")),
        "agency": (STR, None),
        "account_number": (STR, None),
        "active": (BOOL, True),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }