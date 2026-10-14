from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    RecurrenceFrequency,
    RecurrenceStatus,
    TransactionType,
)
from app.schemas.account import validate_money


class RecurringBase(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    type: TransactionType
    amount: Decimal = Field(gt=0)
    frequency: RecurrenceFrequency
    start_date: date
    end_date: Optional[date] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    card_id: Optional[str] = None

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str) -> str:
        return v.strip()

    @field_validator("amount")
    @classmethod
    def clean_amount(cls, v: Decimal) -> Decimal:
        return validate_money(v)

    @field_validator("start_date", mode="before")
    @classmethod
    def clean_start(cls, v) -> date:
        return date.fromisoformat(str(v))

    @field_validator("end_date", mode="before")
    @classmethod
    def clean_end(cls, v) -> date | None:
        if not v:
            return None
        return date.fromisoformat(str(v))


class RecurringCreate(RecurringBase):
    pass


class RecurringUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=160)
    type: Optional[TransactionType] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    frequency: Optional[RecurrenceFrequency] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    status: Optional[RecurrenceStatus] = None
    next_due_date: Optional[date] = None


class RecurringRead(RecurringBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    next_due_date: date
    status: RecurrenceStatus
    last_generated_at: Optional[date] = None
    generated_count: int = 0
    