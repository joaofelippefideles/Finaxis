from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import InstallmentStatus
from app.schemas.account import validate_money
from app.schemas.transaction import TransactionRead


class InstallmentCreate(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    total_value: Decimal = Field(gt=0)
    installments_total: int = Field(ge=2, le=120)
    first_due_date: date
    category_id: Optional[str] = None
    card_id: Optional[str] = None
    observation: Optional[str] = Field(default=None, max_length=500)

    @field_validator("total_value")
    @classmethod
    def clean_value(cls, v: Decimal) -> Decimal:
        return validate_money(v)

    @field_validator("first_due_date", mode="before")
    @classmethod
    def clean_date(cls, v) -> date:
        return date.fromisoformat(str(v))


class InstallmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    description: str
    total_value: Decimal
    installments_total: int
    first_due_date: date
    category_id: Optional[str] = None
    card_id: Optional[str] = None
    status: InstallmentStatus
    observation: Optional[str] = None
    paid_count: int = 0
    paid_total: Decimal = Decimal("0")
    parcels: list[TransactionRead] = []