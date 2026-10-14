from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ListItemStatus, RecurrenceFrequency
from app.schemas.account import validate_money


class ListItemBase(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    amount: Decimal = Field(gt=0)
    due_date: date
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    frequency: Optional[RecurrenceFrequency] = None
    observation: Optional[str] = Field(default=None, max_length=500)

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str) -> str:
        return v.strip()

    @field_validator("amount")
    @classmethod
    def clean_amount(cls, v: Decimal) -> Decimal:
        return validate_money(v)

    @field_validator("due_date", mode="before")
    @classmethod
    def clean_date(cls, v) -> date:
        return date.fromisoformat(str(v))


class PayableCreate(ListItemBase):
    pass


class PayableUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=160)
    amount: Optional[Decimal] = Field(default=None, gt=0)
    due_date: Optional[date] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    frequency: Optional[RecurrenceFrequency] = None
    observation: Optional[str] = Field(default=None, max_length=500)
    status: Optional[ListItemStatus] = None

    @field_validator("amount")
    @classmethod
    def clean_amount(cls, v: Decimal | None) -> Decimal | None:
        return validate_money(v) if v is not None else v

    @field_validator("due_date", mode="before")
    @classmethod
    def clean_date(cls, v) -> date | None:
        return date.fromisoformat(str(v)) if v else None


class PayableRead(ListItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: ListItemStatus
    paid_at: Optional[date] = None
    is_overdue: bool = False


class ReceivableCreate(ListItemBase):
    pass


class ReceivableUpdate(PayableUpdate):
    pass


class ReceivableRead(ListItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: ListItemStatus
    received_at: Optional[date] = None
    is_overdue: bool = False