from datetime import datetime
from decimal import Decimal

from app.models.base import DATE, DATETIME, DECIMAL, ENUM, INT, STR, JsonModel, gen_uuid
from app.models.enums import InstallmentStatus

MONEY = DECIMAL


class Installment(JsonModel):
    """Compra parcelada: grupo que agrega as parcelas (cada parcela é uma Transaction)."""

    COLLECTION = "installments"
    _fields = {
        "id": (STR, gen_uuid),
        "user_id": (STR, None),
        "description": (STR, None),
        "total_value": (DECIMAL, Decimal("0")),
        "installments_total": (INT, 1),
        "first_due_date": (DATE, None),
        "category_id": (STR, None),
        "card_id": (STR, None),
        "status": ((ENUM, InstallmentStatus), InstallmentStatus.active),
        "observation": (STR, None),
        "created_at": (DATETIME, datetime.now),
        "updated_at": (DATETIME, datetime.now),
    }