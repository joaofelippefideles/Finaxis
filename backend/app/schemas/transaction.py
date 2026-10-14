from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TransactionStatus, TransactionType
from app.schemas.account import validate_money


def parse_date(v: str | date) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    return date.fromisoformat(str(v))


class TransactionBase(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    amount: Decimal = Field(gt=0)
    type: TransactionType
    date: date
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    status: TransactionStatus = TransactionStatus.pending
    observation: Optional[str] = Field(default=None, max_length=500)
    installments_total: Optional[int] = Field(default=None, ge=2, le=120)

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("A descrição é obrigatória")
        return v

    @field_validator("amount")
    @classmethod
    def clean_amount(cls, v: Decimal) -> Decimal:
        return validate_money(v)

    @field_validator("date", mode="before")
    @classmethod
    def clean_date(cls, v) -> date:
        return parse_date(v)


class TransactionCreate(TransactionBase):
    is_installment: Optional[bool] = False


class TransferCreate(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    amount: Decimal = Field(gt=0)
    from_account_id: str
    to_account_id: str
    date: date
    observation: Optional[str] = Field(default=None, max_length=500)

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("A descrição é obrigatória")
        return v

    @field_validator("amount")
    @classmethod
    def clean_amount(cls, v: Decimal) -> Decimal:
        return validate_money(v)

    @field_validator("date", mode="before")
    @classmethod
    def clean_date(cls, v) -> date:
        return parse_date(v)


class TransactionUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=160)
    amount: Optional[Decimal] = Field(default=None, gt=0)
    date: Optional[date] = None
    category_id: Optional[str] = None
    account_id: Optional[str] = None
    card_id: Optional[str] = None
    status: Optional[TransactionStatus] = None
    observation: Optional[str] = Field(default=None, max_length=500)

    @field_validator("amount")
    @classmethod
    def clean_amount(cls, v: Decimal | None) -> Decimal | None:
        return validate_money(v) if v is not None else v

    @field_validator("date", mode="before")
    @classmethod
    def clean_date(cls, v) -> date | None:
        return parse_date(v) if v else None


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    installment_id: Optional[str] = None
    installment_number: Optional[int] = None
    recurring_id: Optional[str] = None
    paid_at: Optional[date] = None
    is_installment: bool = False
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    created_at: datetime
    category_name: Optional[str] = None
    account_name: Optional[str] = None
    card_name: Optional[str] = None