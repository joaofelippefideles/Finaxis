from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CardStatus
from app.schemas.account import validate_money


class CreditCardBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    bank: Optional[str] = Field(default=None, max_length=80)
    limit_amount: Decimal = Field(default=Decimal("0"))
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)
    account_id: Optional[str] = None
    status: CardStatus = CardStatus.active

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("limit_amount")
    @classmethod
    def clean_limit(cls, v: Decimal) -> Decimal:
        return validate_money(v)


class CreditCardCreate(CreditCardBase):
    pass


class CreditCardUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    bank: Optional[str] = Field(default=None, max_length=80)
    limit_amount: Optional[Decimal] = None
    closing_day: Optional[int] = Field(default=None, ge=1, le=31)
    due_day: Optional[int] = Field(default=None, ge=1, le=31)
    account_id: Optional[str] = None
    status: Optional[CardStatus] = None

    @field_validator("limit_amount")
    @classmethod
    def clean_limit(cls, v: Decimal | None) -> Decimal | None:
        return validate_money(v) if v is not None else v


class CreditCardRead(CreditCardBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    used_limit: Decimal = Decimal("0")
    available_limit: Decimal = Decimal("0")
    current_invoice: Decimal = Decimal("0")
    next_invoice: Decimal = Decimal("0")


class CardInvoice(BaseModel):
    month: str
    due_date: str | None = None
    total: Decimal = Decimal("0")
    items: list[dict] = []


class CardPaymentResult(BaseModel):
    invoice: str
    paid_total: Decimal = Decimal("0")
    transactions: list[str] = []